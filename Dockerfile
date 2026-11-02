FROM python:3.14.7-slim-trixie@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 PATH=/app/.venv/bin:$PATH
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev --no-cache
COPY proxy proxy
RUN install -d -o 65534 -g 65534 /var/lib/metrics
USER 65534
CMD ["python", "-m", "proxy"]
