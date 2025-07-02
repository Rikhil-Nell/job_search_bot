# Best practice: Define uv version as an argument for flexibility and reproducibility [1]
ARG UV_VERSION=0.7.18

# Stage 1: builder - for installing dependencies and the project
# This stage contains build tools and is discarded in the final image [8].
FROM python:3.13-slim-bookworm AS builder

# Install uv by copying the binary from the official distroless Docker image [2].
COPY --from=ghcr.io/astral-sh/uv:${UV_VERSION} /uv /uvx /bin/

# Set working directory for the builder stage [user's original]
WORKDIR /app

# Install system dependencies needed for building Python packages (e.g., compilation tools)
# If your project has binary dependencies or needs specific OS libraries.
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Best practice: Copy only the dependency definition files first for better caching [9].
# uv.lock is crucial for reproducible builds with uv sync [7].
# pyproject.toml defines your project and its core dependencies.
COPY pyproject.toml uv.lock ./

# Install project dependencies.
# --mount=type=cache,target=/root/.cache/uv: Caches uv's downloads across builds [5].
# --locked: Ensures uv respects the uv.lock file, guaranteeing reproducibility [7].
# --no-install-project: Installs dependencies but not the project itself in this layer [9].
# --no-editable: Installs packages in non-editable mode, ideal for production [8, 10].
# --compile-bytecode: Compiles Python source to bytecode for faster startup [11].
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable --compile-bytecode

# Copy the entire project code into the builder stage [user's original].
ADD . /app

# Sync the project itself into the environment.
# Since dependencies were already installed, this step is very fast [9].
# --no-editable: Again, for production builds, removing dependency on source code in final image [8, 10].
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --compile-bytecode

# Important: Add .venv to your .dockerignore file to prevent local virtual environments from being copied [7].

# Stage 2: final - a minimal image containing only the application and its virtual environment
# This significantly reduces the final image size and attack surface [8].
FROM python:3.13-slim-bookworm

# Set working directory for the final stage [user's original]
WORKDIR /app

# Copy only the compiled virtual environment from the builder stage [8].
# This creates a lean final image with just what's needed to run.
# Consider creating an 'app' user and chowning the directory for better security,
# though the source example uses `--chown=app:app` without defining the user explicitly [8].
COPY --from=builder /app/.venv /app/.venv

# Ensure the installed binaries (like uvicorn) from the virtual environment are on PATH [6].
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port uvicorn will run on [user's original].
EXPOSE 8000

# Start the FastAPI server [user's original].
# uvicorn will be found because its path is in ENV PATH.
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]