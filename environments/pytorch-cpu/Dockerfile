# pytorch-cpu: PyTorch (CPU build) + Hugging Face Transformers and Datasets.
# Honest about what it is: CPU-only — sized for inference, eval harnesses,
# tokenizer and dataset work, not for training large models.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1

# CPU wheels come from the PyTorch CPU index (much smaller than the CUDA build).
RUN pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu

RUN pip install \
    transformers==5.13.1 \
    datasets==5.0.0

# Warm the import caches so forks start hot.
RUN python -c "import torch, transformers, datasets; assert not torch.cuda.is_available(); print('pytorch-cpu ready:', torch.__version__)"

WORKDIR /workspace
CMD ["sleep", "infinity"]
