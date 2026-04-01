# Build stage: compile the Rust extension and build a wheel
FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder

WORKDIR /app

# Install Rust
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:$PATH"

# Cache dependency layers before copying source
COPY Cargo.toml Cargo.lock ./
COPY src/connect_four_rs/Cargo.toml src/connect_four_rs/Cargo.toml
RUN mkdir -p src/connect_four_rs/src && \
    echo 'fn main() {}' > src/connect_four_rs/src/lib.rs && \
    cargo fetch

# Copy full source and build a wheel with maturin
COPY pyproject.toml uv.lock ./
COPY src/ src/

RUN uv tool install maturin && maturin build --release --out /wheels

# Runtime stage: slim Python image, no Rust toolchain
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS runtime

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/connect_four/ src/connect_four/
COPY --from=builder /wheels /wheels

# Install the pre-built wheel (skip maturin build, use the compiled .so directly)
RUN uv pip install --system /wheels/*.whl && \
    rm -rf /wheels

ENTRYPOINT ["python", "-m", "connect_four"]
CMD ["--help"]
