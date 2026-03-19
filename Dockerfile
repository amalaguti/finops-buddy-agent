FROM python:3.11-slim

# System dependencies for WeasyPrint (PDF export) and pycairo build
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Runtime libraries for WeasyPrint
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    fonts-liberation \
    fonts-dejavu-core \
    # Build dependencies for pycairo
    gcc \
    libcairo2-dev \
    libffi-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and uv (for MCP servers)
RUN pip install --no-cache-dir poetry uv

WORKDIR /app

# Optional: pass git SHA at build time for version display (e.g. docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD))
ARG GIT_SHA
ENV FINOPS_GIT_SHA=${GIT_SHA}

# Copy project files needed for installation
COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/
COPY config/ ./config/

# Install dependencies and the project itself
# Disable virtualenv creation to install to system Python
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Expose the API/UI port
EXPOSE 8000

# Run the server (host binding configured via FINOPS_SERVER_HOST env var)
CMD ["poetry", "run", "finops", "serve"]
