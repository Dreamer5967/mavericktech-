"""Bounded real ViLT input-gradient diagnostics on recorded CARLA images.

Measures clean-answer prediction flips, not accuracy without human answer labels.
All perturbation bounds are measured in raw RGB [0,1] space. No simulator access.
"""
import argparse,hashlib,json,time,os
from pathlib import Path
os.environ.setdefault('HF_HOME',str(Path(__file__).resolve().parents[2]/'local-models/huggingface'))
import numpy as np
import torch
from PIL import Image
from transformers import ViltProcessor,ViltForQuestionAnswering


def run(args):
 args.output.mkdir(parents=True,exist_ok=False);torch.set_num_threads(2)
 model_id='dandelin/vilt-b32-finetuned-vqa'
 processor=ViltProcessor.from_pretrained(model_id)
 model=ViltForQuestionAnswering.from_pretrained(model_id).eval()
 for parameter in model.parameters():parameter.requires_grad_(False)
 mean=torch.tensor(processor.image_processor.image_mean).view(1,3,1,1)
 std=torch.tensor(processor.image_processor.image_std).view(1,3,1,1)
 samples=json.loads(args.samples.read_text(encoding='utf-8'));rows=[]
 for sample in samples:
  image=Image.open(sample['image']).convert('RGB');encoded=processor(image,sample['question'],return_tensors='pt')
  pixels=encoded['pixel_values'];original=(pixels*std+mean).clamp(0,1)
  def predict(raw,gradient=False):
   inputs={**encoded,'pixel_values':(raw-mean)/std}
   return model(**inputs).logits
  started=time.monotonic()
  with torch.no_grad():clean=predict(original);label=int(clean.argmax(-1));clean_answer=model.config.id2label[label]
  target=torch.tensor([label])
  for method,iterations in [('clean',0),('fgsm',1),('pgd',4)]:
   adversarial=original.clone()
   for _ in range(iterations):
    adversarial=adversarial.detach().requires_grad_(True)
    loss=torch.nn.functional.cross_entropy(predict(adversarial),target)
    gradient=torch.autograd.grad(loss,adversarial)[0]
    alpha=args.epsilon if method=='fgsm' else args.epsilon/3
    adversarial=(adversarial+alpha*gradient.sign()).detach()
    adversarial=torch.max(torch.min(adversarial,original+args.epsilon),original-args.epsilon).clamp(0,1)
   with torch.no_grad():logits=predict(adversarial);answer=model.config.id2label[int(logits.argmax(-1))]
   # A concrete JPEG preprocessing condition; no claim of certified defense.
   import io
   array=(adversarial[0].permute(1,2,0).numpy()*255).round().astype(np.uint8)
   buffer=io.BytesIO();Image.fromarray(array).save(buffer,format='JPEG',quality=75)
   defended_image=Image.open(io.BytesIO(buffer.getvalue())).convert('RGB')
   defended_inputs=processor(defended_image,sample['question'],return_tensors='pt')
   with torch.no_grad():defended=model.config.id2label[int(model(**defended_inputs).logits.argmax(-1))]
   row={'sample_id':sample['id'],'image_sha256':hashlib.sha256(Path(sample['image']).read_bytes()).hexdigest(),
    'question':sample['question'],'model':model_id,'model_revision':getattr(model.config,'_commit_hash',None),
    'method':method,'epsilon_raw_rgb':args.epsilon,'measured_linf':float((adversarial-original).abs().max()),
    'clean_answer':clean_answer,'answer':answer,'prediction_flipped':answer!=clean_answer,
    'jpeg75_answer':defended,'jpeg75_prediction_flipped':defended!=clean_answer,
    'wall_elapsed_s':time.monotonic()-started,'accuracy':None,'accuracy_note':'No human answer labels; prediction consistency only.'}
   assert row['measured_linf']<=args.epsilon+1e-6
   rows.append(row);print('VILT',json.dumps(row),flush=True)
   (args.output/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 return rows


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--samples',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--epsilon',type=float,default=8/255)
 args=p.parse_args()
 if not 0<args.epsilon<=16/255:p.error('Bound epsilon to at most 16/255.')
 run(args)

if __name__=='__main__':main()
