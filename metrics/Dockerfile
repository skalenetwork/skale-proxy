FROM python:3.13.9-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN mkdir /usr/src/metrics /data
WORKDIR /usr/src/metrics

COPY pyproject.toml ./

RUN uv pip install --prerelease=allow --system --no-cache .

FROM python:3.13.9-slim-trixie

WORKDIR /usr/src/metrics

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV PYTHONPATH="/usr/src/metrics:/usr/lib/python3/dist-packages/"
ENV COLUMNS=80

CMD ["python", "/usr/src/metrics/src/main.py"]