FROM python:3.13.0-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uv /usr/bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    aptitude locate apt-file nano vim git zip unzip wget curl tini \
    graphviz unixodbc-dev gcc g++ flex bison pkg-config automake autoconf cmake \
    libopenblas-dev liblapack-dev libboost-all-dev libncurses5-dev libtool \
    libssl-dev libjemalloc-dev libxml2-dev libxslt-dev libfreetype6-dev \
    libsuitesparse-dev libclang-16-dev llvm-16-dev libthrift-dev libfftw3-dev \
    coinor-libcbc-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY . .

RUN uv sync --frozen --no-dev

CMD ["/bin/bash"]
