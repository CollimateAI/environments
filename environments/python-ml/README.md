# python-ml

Python 3.12 with the classic scientific stack: NumPy 2.5, pandas 3.0, SciPy
1.18, scikit-learn 1.9, Matplotlib 3.11 (Agg backend, headless-ready).

**Best for:** data analysis tasks, classic ML training/eval, code-execution
agents that need the scientific stack without a deep-learning runtime.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("python-ml")
r = client.exec(sb["id"], commands=[["bash", "-lc", """
python - <<'PY'
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
X, y = load_iris(return_X_y=True)
print(RandomForestClassifier(random_state=0).fit(X, y).score(X, y))
PY
"""]])
print(r["stdout"])
```

All libraries are imported once at build time, so the first exec in every fork
starts with warm import caches.
