# go

Go 1.23 with golangci-lint v2.12 on the path.

**Best for:** Go coding agents and lint-gated code generation — grade a
candidate not just on "tests pass" but on "tests pass and the linter is clean".

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("go")
r = client.exec(
    sb["id"],
    files=[{"path": "/workspace/hello/main.go",
            "content": "package main\n\nimport \"fmt\"\n\nfunc main() { fmt.Println(\"hello\") }\n"}],
    commands=[["bash", "-lc",
               "cd /workspace/hello && go mod init hello && go vet ./... && golangci-lint run ./... && go run ."]],
    timeout_seconds=120,
)
print(r["stdout"])
```

The toolchain is proven at build time (a real `go test` and a real
`golangci-lint run`). Module downloads follow your sandbox's egress policy —
for fully offline work, vendor your dependencies or bake them into your own
template.
