FROM python:3.14.10-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 PATH=/app/.venv/bin:$PATH
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv:0.13.8@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85,source=/uv,target=/bin/uv \
    uv sync --locked --no-dev --no-cache
COPY proxy proxy
RUN install -d -o 65534 -g 65534 /var/lib/metrics
USER 65534
CMD ["python", "-m", "proxy"]
