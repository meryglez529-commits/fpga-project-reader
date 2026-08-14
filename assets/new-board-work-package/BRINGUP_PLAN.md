# Bring-up plan

## Scope and order

| Order | Demo | Question answered | Inputs/dependencies | Safe board behavior | Gate |
|---:|---|---|---|---|---|
| 1 | `<demo>` | `<bounded-question>` | `<dependencies>` | `<safe-defaults>` | `<gate>` |

## Product-baseline promotion plan

| Verified asset | Expected class | Canonical destination | Product consumer |
|---|---|---|---|
| | `BOARD_FACT` / `REUSABLE_CORE` / `VENDOR_CONFIG` / `TEST_ONLY` | | |

## Authorization boundary

- Official source writes: `<authorized-scope>`
- Board programming/operation: `<authorized-or-not>`
- Hardware-fault boundary: capture decisive evidence, then move to `hardware-handoff/`.
