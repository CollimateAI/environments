# node

Node.js 22 with pnpm 11 (via corepack), TypeScript 7, and Vitest 4 as global
CLIs.

**Best for:** JS/TS coding agents, test-driven code generation, and any
workflow shaped like "write TypeScript, typecheck it, run the tests".

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("node")
r = client.exec(
    sb["id"],
    files=[
        {"path": "/workspace/fizz.ts",
         "content": "export const fizz = (n: number) => n % 3 === 0 ? 'fizz' : String(n);\n"},
        {"path": "/workspace/fizz.test.ts",
         "content": "import { expect, test } from 'vitest';\nimport { fizz } from './fizz';\ntest('fizz', () => expect(fizz(9)).toBe('fizz'));\n"},
    ],
    commands=[["bash", "-lc", "cd /workspace && tsc --strict --noEmit fizz.ts && vitest run"]],
)
print(r["stdout"])
```

The toolchain is smoke-tested at image build time (a real `tsc` typecheck and
a real `vitest run`), so a green build means a working sandbox.
