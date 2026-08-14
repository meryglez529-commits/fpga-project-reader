# Mode 3 handoff

- State: `NOT_READY`
- Official design root: `<path>`
- Product project: `<path>`
- Product top / part: `<top>` / `<part>`
- Canonical build entry: `<command-or-script>`
- Canonical simulation entry: `<command-script-or-NOT_APPLICABLE>`
- Tool/IP versions: `<versions>`
- Source identity: `<git-revision-or-hash-manifest>`
- Board contract identity: `<revision-or-hash>`
- Acceptance matrix identity: `<revision-or-hash>`
- Qualified release: `<release-manifest-entry-or-NONE>`

## Shared sources and regressions

Link `DEMO_DEPENDENCY_MATRIX.md` and list the canonical board/interface sources Mode 3 may change.

## Excluded assets

List every relevant `TEST_ONLY`, `GENERATED`, and `OBSOLETE` asset that must not enter product source.

## Remaining work and blockers

Separate product feature work from hardware or external blockers.

Declare `MODE3_READY` only after the Mode 4 validator passes all readiness gates.
