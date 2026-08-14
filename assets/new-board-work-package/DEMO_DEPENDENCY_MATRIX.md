# Demo dependency matrix

| Canonical source/configuration | Asset class | Demo consumers | Product consumers | Change invalidates | Latest qualified identity |
|---|---|---|---|---|---|
| `<official-path>` | `BOARD_FACT` / `REUSABLE_CORE` / `VENDOR_CONFIG` | `<demos>` | `<product-scope>` | `<demo/product regressions>` | `<revision-or-hash>` |

Before Mode 3 edits a shared path, mark every mapped qualified demo `STALE`. Demo-only tops and checkers must not appear as product consumers.
