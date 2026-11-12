"""Check installed packages without starting CARLA or downloading model weights.

Run with the environment's explicit Python path. --require-cuda checks CUDA
availability only; a real rendered CARLA RGB frame is a separate required gate.
"""
import argparse
import importlib
from importlib import metadata
import json
import platform
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stack', choices=('sim', 'vqa'), required=True)
    parser.add_argument('--require-cuda', action='store_true')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 10):
        raise SystemExit('Cloud profile expects Python 3.10; use the explicit venv interpreter.')
    packages = {
        'sim': ('carla', 'traci', 'sumolib', 'ultralytics', 'fastapi', 'uvicorn', 'torch', 'torchvision'),
        'vqa': ('torch', 'torchvision', 'transformers', 'langfuse'),
    }[args.stack]
    versions = {}
    for name in packages:
        importlib.import_module(name)
        versions[name] = metadata.version(name)
    if args.stack == 'sim' and versions['carla'] != '0.9.15':
        raise SystemExit('Expected carla==0.9.15 to match the selected server.')
    if args.stack == 'vqa':
        from transformers import ViltForQuestionAnswering, ViltProcessor  # noqa: F401
    import torch
    cuda_ok = torch.cuda.is_available()
    mps_ok = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    if args.require_cuda and not cuda_ok:
        raise SystemExit('CUDA unavailable in this environment. Check driver and installed PyTorch build.')
    print(json.dumps({
        'status': 'IMPORT_CHECK_ONLY', 'stack': args.stack,
        'python': sys.executable, 'platform': platform.platform(),
        'versions': versions, 'cuda_available': cuda_ok, 'mps_available': mps_ok,
        'carla_rendering_validated': False,
    }, indent=2))


if __name__ == '__main__':
    main()
