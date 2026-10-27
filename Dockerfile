FROM python:3.14-slim

ARG YOUR_ENV

ENV YOUR_ENV=${YOUR_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  UV_COMPILE_BYTECODE=1

# Install uv from official binary image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

# Install dependencies first for better layer caching
COPY pyproject.toml uv.lock README.md /code/
RUN if [ "$YOUR_ENV" = "production" ]; then \
      uv sync --frozen --no-dev --no-install-project; \
    else \
      uv sync --frozen --no-install-project; \
    fi

# Copy application source code and install project
COPY wurzelbot /code/wurzelbot
RUN if [ "$YOUR_ENV" = "production" ]; then \
      uv sync --frozen --no-dev; \
    else \
      uv sync --frozen; \
    fi

ENTRYPOINT [ "uv", "run", "python", "wurzelbot" ]
