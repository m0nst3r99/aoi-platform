# Historical provenance limitations — checkpoint preparation

Recorded 2026-10-20. This note supplements immutable evidence; it does not
replace hashes, assert recovery, or grant review acceptance.

## Unrecovered historical versions

| Evidence record | Recorded script | Expected SHA-256 |
| --- | --- | --- |
| [review-01](evidence/review-01/environment-command.json) | `native_case.py` | `24a7e6f7ed4b8ffdb3a11afd379b8e08945a48de322f41fa7f1cc5f42f4e52bf` |
| [review-01](evidence/review-01/environment-command.json) | `test_native.py` | `8d334ef1486b2c5ee255e145504e3b7f9ef1e948fd953b9adbebcf34bc14ccd0` |
| [review-02](evidence/review-02/environment-command.json) | `test_native.py` | `975962e20f7e496ef2459b16e9bf8ad61cd7445cfd24d3974cd24338a143c45d` |

No exact-byte copy was found. Do not substitute current versions, reconstruct
old versions, normalize line endings to manufacture a match, or rewrite these
expected digests. The recorded results remain historical observations, but these
three script versions cannot currently be independently replayed byte-for-byte.

## Recovery search performed

- Inspected all Git refs/history and reflogs, including `refs/agents/.../checkpoints`.
- Ran read-only `git fsck --full --no-reflogs --unreachable`; it reported no
  unreachable objects. Hashed all 890 available Git blobs using
  `git cat-file --batch-all-objects` and `git cat-file --batch`.
- Hashed 1,226 file members in 17 existing root review ZIPs.
- Searched the AOI platform/reference project trees for `native_case.py` and
  `test_native.py`; only the current evaluation copies were found.
- Searched this conversation's available agent-session files for these script
  names and ZIP/TAR/7z snapshots; no candidates were found.

This describes accessible local material, not every possible backup or remote.
No network recovery, installation, evidence editing or Git history changes were
performed. A future exact-hash recovery may supplement this note with its origin.

## Checkpoint interpretation

The preceding audit resolved content for 597 of 600 recorded SHA-256 references:
111 matched staged content, 481 matched preserved archive content, and 5 matched
external artifacts. Archive/external matches are not a claim that all referenced
bytes are included in this Git checkpoint. The three remaining references above
must stay explicitly unresolved.

All 796 original evaluation blobs were verified byte-identical to their working
files after scoped `-text` attributes and re-staging. All 801 pre-existing staged
working files and all 17 ZIPs were unchanged. This protects available evidence;
it does not repair missing historical versions.

The extra EOF blank line in [bottom_control.py](bottom_control.py) is a genuine
formatting issue, deliberately left unchanged because the script is hashed in
[bottom-01](evidence/bottom-01/report.json). Captured CLI-help trailing spaces and
CRLF endings are raw evidence bytes, not content to clean automatically.
Default staged whitespace checks are therefore not claimed to pass.

The latest regression run during byte-preservation preparation passed 491 tests
with 1 opt-in local-fixture skip; strict OpenSpec validation passed. Those checks
do not establish complete historical provenance, general parser compatibility,
or complete Windows containment. Geometry tasks 1.5/5.2 remain PARTIAL.

Commit approval must explicitly acknowledge this documented historical
limitation. No commit or push is authorized by this note.
