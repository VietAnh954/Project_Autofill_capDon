# Changelog

> Auto-generated từ git tag. Mỗi entry tương ứng 1 release.

## :material-tag: v0.0.1-bootstrap — 2026-05-14

**Phase 0 hoàn tất.**

### Added

- `CLAUDE.md` instruction cho Claude Code auto-loop.
- `docs/` đầy đủ 13 file: ARCHITECTURE, CODING_RULES, DATABASE, MAPPING, TECH_STACK, WORKFLOW, GIT_WORKFLOW, DECISIONS, GLOSSARY, TODO, TASKS, SETUP_VSCODE.
- Skeleton `src/auto_fill/` với 7 module: config, mail, reader, mapper, filler, storage, utils.
- VSCode config: `.vscode/settings.json`, `.vscode/extensions.json`, `.vscode/tasks.json`.
- Claude Code config: `.claude/settings.json`, `.claude/commands/{next,status,verify}.md`.
- Build & lint config: `pyproject.toml`, `.pre-commit-config.yaml`, `requirements.txt`.
- Smoke test `tests/test_smoke.py`.

### Upcoming

- Phase 1: MVP Du lịch end-to-end (task 1.1 → 1.17).

---

_Các release sau sẽ tự sinh khi Claude commit + tag từng phase._
