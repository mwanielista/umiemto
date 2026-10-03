# Codex roles and runtime verification

Project roles are defined in `agents/*.toml`: Business Analyst, System Analyst,
Architect and independent Architecture Reviewer. Their common process is in
[workflow.md](../workflow.md); BA/SA artifact contracts are in
[requirements](../docs/requirements/README.md). Restart the Codex session after
changing roles so it loads the current definitions.

## Live role smoke test

Run from repository root with Python 3.11 or later:

```bash
python3.12 .codex/validation/smoke_roles.py
```

Offline fail-closed checks of the report validator (no model usage):

```bash
python3.12 -B .codex/validation/test_smoke_roles.py
```

The test uses the installed, authenticated `codex exec` runtime, strict config
loading and a read-only sandbox. It asks Codex to start four custom-role children
and checks completed collaboration waiting plus unique model-reported child receipts containing
verbatim excerpts from their loaded role instructions (ignoring line wrapping
and whitespace). It fails on reported unavailable
roles or startup failure, timeout or missing/mismatched receipts. Excerpts are not
supplied in the prompts. Temporary response schema files live outside the repo.

This is a live model-attested smoke test, not a deterministic proof of role loading,
every policy or semantic quality. Public CLI events in the tested version expose
completed waits but do not independently correlate all four receipt identities
with their selected role and completed child. The report could therefore falsely
claim startup; matching excerpts and a completed wait alone cannot eliminate that
risk. A stronger integration test needs runtime child/role metadata correlated
with completion. The script prints this evidence limit even on PASS.
It consumes model usage, may initialize Codex's
local state and leaves test sessions in Codex history. It writes no business
analysis or application files. User configuration remains enabled because it
contains project trust. Do not use `--ephemeral` for this test: the tested CLI
requires parent thread state for child spawning. The `--timeout` option defaults
to 300 seconds. Authentication/runtime failures are failures, not skipped passes.

It does not prove that the Desktop app has reloaded its own session, enforce
filesystem locks, validate BA/SA artifacts, or test actual analysis outcomes.
The stdio app-server `config/read` call alone is insufficient: the tested runtime
does not expose custom-role instructions in that response.

Protocol references: [custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Codex app-server](https://learn.chatgpt.com/docs/app-server).
