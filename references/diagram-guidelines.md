# Diagram Guidelines

## Storage Layout

Use source-plus-rendered-image:

```text
AI-work/guide/diagrams/*.d2                 # stable Mode 1/2/as-built diagram source
AI-work/guide/diagrams/*.svg                # rendered stable diagrams
AI-work/features/<feature>/<UNIT>/diagrams/ # Mode 5 working design/verification diagrams
```

Stable guide Markdown should reference SVG files:

```markdown
![图名](diagrams/fpga-overview.svg)
```

## Tool Choice

- Use **D2** for large architecture, top-instance, main data-link, RTM, verification-route, and reading-route diagrams.
- Use **Mermaid** only for small diagrams with six or fewer main nodes, such as reset chain, simple arbitration, remote upgrade, or memory taxonomy.
- Avoid hand-written SVG except for tiny corrections when no diagram tool can express the layout.

## D2 Pattern For FPGA Architecture

Keep real engineering nodes. Improve routing with helper nodes rather than deleting information:

- `控制参数总线`
- `DAC 参数入口`
- `ADC 参数入口`
- `回传总线`
- `支撑总线`
- `remote_* 升级入口`
- local endpoint nodes such as `ETHERNET_TOP 回传口`

Use containers to separate:

1. Control entry / parameter bus
2. Main business data links
3. Support resources

Main data flow should use solid links. Control/support/upgrade relations should use dashed links.

## D2 Visual Semantics

Use consistent colors:

- Control: purple / indigo
- DAC: green
- ADC: blue
- Support: orange
- Memory: neutral slate/gray

Prefer two-line labels at most. Put file paths, detailed signals, and caveats in tables or prose, not nodes.

## Mermaid Rules

For small Mermaid diagrams:

- Use `flowchart LR` or `flowchart TB`.
- Keep labels short.
- Do not use `<br/>` unless absolutely necessary.
- Do not exceed six main-path nodes.
- If it becomes wide or visually important, migrate it to D2.

## Mode 5 Diagram Rule

During feature development, keep requirement sketches, architecture alternatives, state-machine insertions, CDC/FIFO timing diagrams, and ILA observation routes inside the feature unit. Promote only verified final diagrams to `AI-work/guide/diagrams/` or the relevant `*_AS_BUILT.md`.
