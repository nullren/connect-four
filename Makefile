.PHONY: build run play benchmark docker-build docker-run docker-play docker-benchmark

# Local
build:
	uv sync
	uv run maturin develop --release

PLAY_ARGS    ?= --p1 human --p2 perfect
BENCH_ARGS   ?= --p1 minimax --p2 random --games 100

play:
	uv run connect-four play $(PLAY_ARGS)

benchmark:
	uv run connect-four benchmark $(BENCH_ARGS)

test:
	uv run pytest

# Docker
docker-build:
	docker build -t connect-four .

docker-play:
	docker run -it connect-four play $(PLAY_ARGS)

docker-benchmark:
	docker run connect-four benchmark $(BENCH_ARGS)
