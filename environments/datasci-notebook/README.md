# datasci-notebook

Python 3.12 with an installed Jupyter kernel (`ipykernel` + `jupyter-client`),
DuckDB 1.5, Polars 1.42, PyArrow 25, and pandas 3.0.

**Best for:** notebook-style, stateful data work driven entirely through exec.
There is deliberately **no Jupyter server** in this image — nothing listens on
a port. Agents that want notebook semantics start a kernel and talk to it with
`jupyter-client`, or just run Python directly; DuckDB gives you SQL over
Parquet/CSV files without a database server.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("datasci-notebook")
r = client.exec(sb["id"], commands=[["bash", "-lc", """
python - <<'PY'
import duckdb, polars as pl
sales = pl.DataFrame({"region": ["eu", "us", "eu"], "amount": [10, 20, 5]})
print(duckdb.sql("SELECT region, SUM(amount) FROM sales GROUP BY region ORDER BY region").df())
PY
"""]])
print(r["stdout"])
```

A useful pattern with forking: load a big dataset once in a parent sandbox,
then fork it — every child starts with the data already in place, sharing the
memory until it writes.
