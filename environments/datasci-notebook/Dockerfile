# datasci-notebook: Python + a Jupyter kernel (exec-driven, no server) with
# DuckDB, Polars, and PyArrow. Notebook-style stateful execution for dataframe
# agents and SQL-on-files — you talk to the kernel through exec, nothing listens.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install \
    ipykernel==7.3.0 \
    jupyter-client==8.9.1 \
    duckdb==1.5.4 \
    polars==1.42.1 \
    pyarrow==25.0.0 \
    pandas==3.0.3

# Prove the stack at build time: register the kernel and run a real
# DuckDB-over-Polars query.
RUN python -m ipykernel install --name python3 --sys-prefix \
 && python - <<'PY'
import duckdb, polars as pl
df = pl.DataFrame({"x": [1, 2, 3]})
out = duckdb.sql("SELECT SUM(x) AS s FROM df").fetchone()
assert out[0] == 6
print("datasci-notebook ready")
PY

WORKDIR /workspace
CMD ["sleep", "infinity"]
