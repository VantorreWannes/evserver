FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app
COPY . .
RUN uv sync --locked --no-dev
VOLUME /app/data
CMD ["uv", "run", "evserver"]
