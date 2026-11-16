# AOI session rules

- The real repository `C:/dev/aoi-platform` is the source of truth. Chat mirrors
  and earlier messages are context, not proof of the current checkout.
- `master` is the primary development branch; checkpoint branches preserve history
  and evidence. Branch changes, merges, commits and pushes require explicit user
  authorization. Develop against the relevant OpenSpec contracts and tasks.
- At session entry, verify `git rev-parse --show-toplevel`, `git branch --show-current`,
  `git rev-parse HEAD`, and `git status --short`; inspect staged and unstaged diff
  summaries. Preserve all existing edits and untracked files.
- Read the top **Current State / Next Action** section of [HANDOFF.md](HANDOFF.md).
  Compare actual branch/HEAD with its snapshot. If different, inspect the relevant
  branch/log and report the mismatch; do not switch, reset, merge or assume the
  older handoff applies. Ask for branch/task direction when necessary.
- Use progressive disclosure: read only task-relevant sections of
  [implementation status](openspec/changes/board-geometry-foundation/implementation-status.md),
  OpenSpec design/spec/tasks, source and evidence. Use headings/search, bounded
  terminal output and per-file diffs; do not load entire historical logs or chats.
- A Next Action is a proposal, not authorization. Implement only the user's task
  or an explicitly authorized continuation. Do not broaden scope or automatically
  commit/push. Never use unrelated `main` as a base; no merge into `master`, history
  rewrite, branch deletion or protection changes without explicit authorization.
- Never delete or overwrite historical evidence, fixtures, oracles or review ZIPs.
  Use fresh evidence directories. No indiscriminate staging or destructive cleanup.
- Before merges, inventory untracked and ignored local-only artifacts with relative
  paths, sizes and SHA-256 in a safe location outside the repository. Stop on incoming
  path collisions; verify every inventoried file after merging. Never automatically
  move, stage, commit or upload local-only artifacts; report their categories separately.
- Separate tests run now, saved implementer logs and user-relayed review results.
  Record exact scope, paths, exit/results and reviewer rerun limitations. A passing
  subset does not establish complete geometry, import readiness or publication.
  Keep PARTIAL tasks and checkboxes unchanged absent complete evidence and authority.
- At task end or before interruption, refresh Current State / Next Action with
  branch/HEAD, working-tree snapshot, completed work, evidence, limits/blockers and
  one next action with scope/acceptance. Preserve the prior snapshot in the handoff
  history before replacement. Keep implementation status consistent when affected.
- Report changed files, checks actually run, remaining limitations and Git state.
  Docs-only work needs `git diff --check`, not the AOI test suite. Do not alter agent
  configuration outside the explicitly authorized process-documentation scope.

## Documentation and Verification Policy

- Documentation is part of Definition of Done for each authorized implementation
  slice. Update only directly affected documents incrementally alongside code;
  keep changed docstrings, interface contracts and invariants consistent.
- Approved OpenSpec specifications and design decisions are authoritative; code
  must conform. Never silently rewrite requirements to match implementation.
  For a discrepancy, identify the exact conflict and technical impact, propose
  alternatives, and obtain owner approval before changing normative requirements.
- Before proposing tests, consult the affected rows and evidence mappings in the
  [verification matrix](openspec/changes/board-geometry-foundation/verification-matrix.md).
  Reuse historical evidence first. Reruns need a technical reason tied to changed
  source, dependencies, fixtures, oracles, environment or an identified coverage
  gap; session, branch and documentation changes alone are not such a reason.
- After verification, update affected matrix mappings with exact test identities,
  results, evidence paths, provenance, limitations and justified acceptance status.
  Verification and acceptance remain separate; the evidence/authorization rule
  above applies to scenario promotion and task checkbox closure.
- At meaningful slice completion, update implementation status with progress,
  unresolved gaps and blockers. Follow the handoff rule above, keeping its current
  entry concise: repository state, relevant links, unresolved decisions and next
  authorized action (or an explicitly labelled proposal awaiting authorization).
- Prefer relevant sections, precise links and incremental updates. Preserve
  historical records; do not duplicate evidence or create a new documentation
  framework or lengthy session report when authoritative records already suffice.
- Documentation-only work needs no regression tests unless executable
  configuration, generated artifacts or software-consumed contracts change;
  in that case justify the necessary checks within the authorized scope.
- Documentation maintenance grants no authority for unrelated refactoring,
  additional tests, branch operations, commits or pushes. At slice completion,
  report code/documentation changes, actual verification results, remaining
  acceptance gaps and any required owner decision.
