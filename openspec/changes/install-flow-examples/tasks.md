## 1. Package the retained flow examples

- [x] 1.1 Keep only `chat-review` and `dev-test` under `flows/examples/`
- [x] 1.2 Preserve explicit non-normative copy-before-use notices and parity with the current shared flows

## 2. Align initialization contract

- [x] 2.1 Update the Python initializer exact inventory to create the two nested examples
- [x] 2.2 Update the LLM fallback, skill instructions and README to describe the same two-example inventory

## 3. Verification

- [x] 3.1 Update initialization, package-layout, flow and end-to-end tests for the example contract and independent exact inventory
- [x] 3.2 Run strict OpenSpec validation, the full unittest suite and diff checks
