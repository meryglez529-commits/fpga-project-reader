# Mode 2 — Single-File Close Reading and Annotation

Use this mode when the user names one RTL/source file and asks to read, explain, annotate, comment, or compare it. The objective is teaching and traceability without functional behavior changes.

## 1. Boundary

Mode 2 may edit comments in the selected source and its required user-RTL dependency closure. It never changes ports, parameters, logic, constraints, IP, project settings, or generated/third-party code. If close reading exposes a defect or a needed behavior change, record it and open a Mode 3 unit.

## 2. Resolve the annotation closure first

Before editing, resolve the selected module’s directly instantiated **user RTL** modules, then recursively resolve their instantiated user RTL modules until reaching one of these boundaries:

- a leaf source module with no user RTL child;
- generated IP, vendor primitive, encrypted RTL, black box or third-party source;
- a module whose source cannot be uniquely resolved.

For each boundary, record the instance name, module/interface contract, source classification and reason it is not annotated. A child referenced from multiple instances is annotated once and its instance sites are listed. Do not merely follow files included by a compile list: this closure follows actual module instantiation.

## 3. Preserve source format exactly

For every edited file, detect before editing and write into the manifest:

- encoding: UTF-8, UTF-8 with BOM, GBK, GB18030, or other confirmed format;
- line ending: CRLF or LF;
- original module names, ports and a pre-edit content/diff fingerprint.

Write comments in the file’s established language and comment style. Preserve encoding, BOM and line endings when saving. After editing, verify that the functional content is byte-identical apart from inserted/replaced comment ranges: ports, module/interface declarations, parameters, assignments, procedural logic and instantiation statements must be unchanged. If safe format preservation is not possible, stop before writing and report the blocker.

Use `check-source-format.py <source> --write-json AI-work/annotations/<file>.before-format.json` before editing and the same command with `--expected-json` afterwards. The helper never edits RTL and fails if encoding, BOM, or newline convention changes; record its commands and the functional diff review in the annotation manifest.

## 4. Reading workflow

1. Locate the source in the real data path: upstream/downstream, clock/reset, data/control boundary and external interfaces.
2. State one plain-language purpose sentence: “this module does one thing: …”. Explain why before listing signals.
3. Identify real-world data objects and units: pixel/sample/frame/packet, count/address/byte/word, valid versus padded data, lane/channel and trigger boundaries.
4. Explain contracts at module interfaces, state machines, FIFO/CDC boundaries, packing/reordering logic, length arithmetic and non-obvious constants. Do not comment obvious syntax.
5. Add short, concrete comments; for a Chinese user, use clear Chinese consistent with the source’s existing language. Do not add new mojibake or rewrite unrelated legacy text just for style.
6. Validate source structure and the functional-only diff after editing.

## 5. Required manifest

Write `AI-work/annotations/<scope>_ANNOTATION_MANIFEST.md`:

```markdown
# <scope> annotation manifest

| 项目 | 内容 |
|---|---|
| 根源文件 / 模块 | |
| 数据通路位置 | |
| 注释范围 | 根模块及递归例化的用户 RTL 闭包 |
| 未编辑边界 | IP / primitive / generated / third-party / unresolved，含实例与接口说明 |
| 源文件格式 | 每个文件的 encoding、BOM、line ending |
| 实例关系 | 每个模块与所有实例位置 |
| 功能差异检查 | 仅注释文本变更；module/ports/logic 未变 |
| 验证命令与结果 | |
| 后续 Mode 3 问题 | 无 / 链接到 unit |
```

## 6. Final handoff

Tell the user what mental model the comments establish, which sources were annotated, what dependency boundary was intentionally not edited, which format checks passed, and that functional RTL was untouched. Link the manifest.
