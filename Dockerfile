# Best practice: Define uv version as an argument for flexibility and reproducibility
ARG UV_VERSION=0.7.18

# Stage 1: builder - for installing dependencies and the project
# This stage contains build tools and is discarded in the final image
FROM python:3.13-slim-bookworm AS builder

# Install uv by copying the binary from the official distroless Docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory for the builder stage
WORKDIR /app

# Install system dependencies needed for building Python packages (e.g., compilation tools)
# If your project has binary dependencies or needs specific OS libraries.
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Best practice: Copy only the dependency definition files first for better caching
# uv.lock is crucial for reproducible builds with uv sync
# pyproject.toml defines your project and its core dependencies
COPY pyproject.toml uv.lock ./

# Install project dependencies
# --mount=type=cache,target=/root/.cache/uv: Caches uv's downloads across builds
# --locked: Ensures uv respects the uv.lock file, guaranteeing reproducibility
# --no-install-project: Installs dependencies but not the project itself in this layer
# --no-editable: Installs packages in non-editable mode, ideal for production
# --compile-bytecode: Compiles Python source to bytecode for faster startup
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable --compile-bytecode

# Copy the entire project code into the builder stage
ADD . /app

# Sync the project itself into the environment
# Since dependencies were already installed, this step is very fast
# --no-editable: Again, for production builds, removing dependency on source code in final image
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --compile-bytecode

# Stage 2: final - a minimal image containing only the application and its virtual environment
# This significantly reduces the final image size and attack surface
FROM python:3.13-slim-bookworm

# Set working directory for the final stage
WORKDIR /app

# Copy only the compiled virtual environment from the builder stage
# This creates a lean final image with just what's needed to run
COPY --from=builder /app/.venv /app/.venv

# Copy the source code from the builder stage
# This is what was missing - your application code needs to be in the final image
COPY --from=builder /app/src /app/src

# Copy other necessary files (if any)
COPY --from=builder /app/prompt.md /app/prompt.md

# Ensure the installed binaries (like uvicorn) from the virtual environment are on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port uvicorn will run on
EXPOSE 8000

# Start the FastAPI server
# uvicorn will be found because its path is in ENV PATH
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]