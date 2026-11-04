FROM python:3.14.10-slim-trixie@sha256:930e1abba7c4e8f96ed93e8012c35d174d7732752731bbd5e8e757d7ec6f3966
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 PATH=/app/.venv/bin:$PATH
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev --no-cache
COPY proxy proxy
RUN install -d -o 65534 -g 65534 /var/lib/metrics
USER 65534
CMD ["python", "-m", "proxy"]
