FROM python:3.13.9-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /usr/src/proxy

COPY pyproject.toml ./

RUN uv pip install --prerelease=allow --system --no-cache .

FROM python:3.13.9-slim-trixie

WORKDIR /usr/src/proxy

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

ENV PYTHONPATH="/usr/src/proxy:/usr/lib/python3/dist-packages/"
ENV COLUMNS=80

CMD ["python", "/usr/src/proxy/proxy/main.py"]