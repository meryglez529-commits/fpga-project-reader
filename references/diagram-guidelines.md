# Diagram Guidelines

## Storage Layout

Use source-plus-rendered-image:

```text
docs/diagrams/*.d2      # large diagram source
docs/diagrams/*.mmd     # small/legacy Mermaid source if useful
docs/images/*.svg       # rendered diagrams referenced by Markdown
```

Markdown should reference SVG files:

```markdown
![图名](docs/images/fpga-overview.svg)
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
