.PHONY: build run play benchmark docker-build docker-run docker-play docker-benchmark

# Local
build:
	uv sync
	uv run maturin develop --release

play:
	uv run connect-four play $(ARGS)

benchmark:
	uv run connect-four benchmark $(ARGS)

test:
	uv run pytest

# Docker
docker-build:
	docker build -t connect-four .

docker-play:
	docker run -it connect-four play $(ARGS)

docker-benchmark:
	docker run connect-four benchmark $(ARGS)
