# rust

Rust 1.79 (rustc + cargo) with the native build dependencies most real crates
need (`pkg-config`, `libssl-dev`, `git`, `curl`) and
[cargo-nextest](https://nexte.st) 0.9.72 for fast, machine-readable test runs.

**Best for:** Rust code generation, compile-and-test reward loops, and agents
whose grading signal is "does it build, do the tests pass".

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("rust")
r = client.exec(
    sb["id"],
    files=[{"path": "/workspace/smoke/src/lib.rs",
            "content": "pub fn double(x: i64) -> i64 { x * 2 }\n\n#[cfg(test)]\nmod tests {\n    #[test]\n    fn doubles() { assert_eq!(super::double(21), 42); }\n}\n"},
           {"path": "/workspace/smoke/Cargo.toml",
            "content": "[package]\nname = \"smoke\"\nversion = \"0.1.0\"\nedition = \"2021\"\n"}],
    commands=[["bash", "-lc", "cd /workspace/smoke && cargo nextest run"]],
    timeout_seconds=300,
)
print(r["stdout"])
```

Compilation is CPU-heavy; forks are cheap, compiles are not — size your
per-exec timeouts for real `cargo build` times.
