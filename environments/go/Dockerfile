# go: Go 1.23 toolchain + golangci-lint. The Go coding-agent sandbox — build,
# test, and lint-gate generated Go code in one environment.
FROM golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0

ENV CGO_ENABLED=0 \
    GOFLAGS=-mod=mod

# golangci-lint (pinned) via the official installer.
RUN curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/HEAD/install.sh \
      | sh -s -- -b /usr/local/bin v2.12.2 \
 && golangci-lint --version

# Prove the toolchain at build time: init a module, test it, lint it.
RUN mkdir -p /tmp/smoke && cd /tmp/smoke \
 && go mod init smoke \
 && printf 'package smoke\n\nfunc Add(a, b int) int { return a + b }\n' > smoke.go \
 && printf 'package smoke\n\nimport "testing"\n\nfunc TestAdd(t *testing.T) {\n\tif Add(2, 2) != 4 {\n\t\tt.Fatal("math is broken")\n\t}\n}\n' > smoke_test.go \
 && go test ./... \
 && golangci-lint run ./... \
 && cd / && rm -rf /tmp/smoke /root/.cache

WORKDIR /workspace
CMD ["sleep", "infinity"]
