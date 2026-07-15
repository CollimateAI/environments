# python-ml: Python 3.12 + the classic scientific stack (NumPy, pandas, SciPy,
# scikit-learn, Matplotlib). The general-purpose data/ML sandbox — fits code-exec
# agents, analysis tasks, and classic ML without pulling in a deep-learning runtime.
FROM python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

RUN pip install \
    numpy==2.5.1 \
    pandas==3.0.3 \
    scipy==1.18.0 \
    scikit-learn==1.9.0 \
    matplotlib==3.11.0

# Import everything once so first exec in a fork pays no import-compile cost.
RUN python -c "import numpy, pandas, scipy, sklearn, matplotlib.pyplot; print('python-ml ready')"

WORKDIR /workspace
CMD ["sleep", "infinity"]
