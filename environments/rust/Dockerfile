# rust: Rust 1.79 toolchain + common native build deps + cargo-nextest.
# The compile-and-test sandbox for Rust codegen and reward loops that grade
# by "does it build, do the tests pass".
FROM rust:1.79-slim@sha256:073c8e7ae12d2637d1d541cb0f3f9d92bfa22c97e2e45db87a9fc6a90c9a7f22

# Common native deps most real crates need at build time (openssl-sys, pkg-config,
# git dependencies), then drop the apt lists.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      libssl-dev \
      pkg-config \
 && rm -rf /var/lib/apt/lists/*

# cargo-nextest (pinned): faster, cleaner test runs than `cargo test`.
RUN curl -LsSf https://get.nexte.st/0.9.72/linux | tar zxf - -C /usr/local/bin \
 && cargo nextest --version

# Prove the toolchain at build time: build and test a real crate.
RUN cargo new /tmp/smoke --lib \
 && cd /tmp/smoke \
 && cargo nextest run \
 && cd / && rm -rf /tmp/smoke /usr/local/cargo/registry/cache

WORKDIR /workspace
CMD ["sleep", "infinity"]
