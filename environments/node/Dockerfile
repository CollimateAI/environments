# node: Node.js 22 + pnpm, TypeScript, and Vitest. The JS/TS coding-agent
# sandbox — write code, typecheck it, test it, all in one warm environment.
FROM node:22-slim@sha256:6c74791e557ce11fc957704f6d4fe134a7bc8d6f5ca4403205b2966bd488f6b3

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0

# pnpm via corepack (pinned), TypeScript + Vitest as global CLIs (pinned).
RUN corepack enable \
 && corepack prepare pnpm@11.13.0 --activate \
 && npm install -g typescript@7.0.2 vitest@4.1.10 \
 && npm cache clean --force

# Prove the toolchain end-to-end at build time: typecheck + run a real test.
RUN mkdir -p /tmp/smoke && cd /tmp/smoke \
 && printf 'export const add = (a: number, b: number): number => a + b;\n' > add.ts \
 && printf 'import { expect, test } from "vitest";\nimport { add } from "./add";\ntest("add", () => { expect(add(2, 2)).toBe(4); });\n' > add.test.ts \
 && tsc --strict --noEmit add.ts \
 && vitest run --root /tmp/smoke \
 && rm -rf /tmp/smoke

WORKDIR /workspace
CMD ["sleep", "infinity"]
