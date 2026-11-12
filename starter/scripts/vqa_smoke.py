"""Local model smoke test. Downloads model files; not a benchmark."""
import argparse
from PIL import Image
import torch
from transformers import ViltProcessor, ViltForQuestionAnswering

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',required=True)
    p.add_argument('--question',required=True)
    p.add_argument('--model',default='dandelin/vilt-b32-finetuned-vqa')
    a=p.parse_args()
    image=Image.open(a.image).convert('RGB')
    if image.width*image.height > 20_000_000:
        raise SystemExit('Use a smaller test image.')
    processor=ViltProcessor.from_pretrained(a.model)
    model=ViltForQuestionAnswering.from_pretrained(a.model).eval()
    inputs=processor(image,a.question,return_tensors='pt')
    with torch.no_grad():
        logits=model(**inputs).logits
    idx=int(logits.argmax(-1).item())
    print({'model':a.model,'answer':model.config.id2label[idx],
           'status':'SMOKE_TEST_ONLY','device':'cpu'})
if __name__=='__main__':main()
