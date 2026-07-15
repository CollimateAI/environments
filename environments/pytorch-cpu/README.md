# pytorch-cpu

PyTorch 2.13 (CPU build) with Transformers 5.13 and Datasets 5.0.

**Best for:** CPU inference on small models, eval harnesses, tokenizer work,
dataset preprocessing, and reward-model plumbing. This is deliberately the CPU
build — it keeps the image small and the forks cheap. It is not a training
environment for large models, and it doesn't pretend to be.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("pytorch-cpu")
r = client.exec(sb["id"], commands=[["bash", "-lc", """
python - <<'PY'
import torch
x = torch.randn(64, 64)
print((x @ x.T).diagonal().sum().item())
PY
"""]], timeout_seconds=60)
print(r["stdout"])
```

Model downloads from the Hugging Face Hub work when your sandbox's egress
policy allows it; for fully offline eval, bake the weights into your own
template (see "Bring your own environment" in the root README).
