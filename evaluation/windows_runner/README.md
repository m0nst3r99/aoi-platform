# Bounded Windows runner: evaluation only

Entry point: `runner.run_bounded_worker(Request) -> ExecutionSuccess | ExecutionFailure`.
[Types](models.py) are frozen; [Win32 binding](winapi.py) declares x64 layouts and
prototypes. [Runner](runner.py) has no KiCad, JSON, inventory bridge or product
dependency. Caller supplies an already staged, stable read-only disk handle,
size/hash and artifact/source IDs. Caller owns that handle and file; the runner
duplicates the handle and never deletes input. The `{staged_handle}` argument
token passes the duplicate to a trusted helper. Duplicate file offsets are shared:
the caller must not concurrently seek/read. Validation maps read-only, in chunks.

Absolute executable/cwd and explicit immutable argv/environment are mandatory;
stdin is NUL. Only the staged duplicate, NUL and output writers inherit. Job limits
are set and queried before suspended creation/assignment/resume. No Job handle
inheritance or breakaway. Output is raw bounded bytes; malformed JSON can succeed.
Success requires root exit zero, both EOF, Job accounting active count zero, no
observed errors, and confirmed cleanup. Failure prefixes are explicitly unusable.
The entry deadline includes validation; cleanup has its own deadline. Acquisition
and staging are outside this API. This is not a filesystem/network/security sandbox.

## Reproduce

From repository root (Windows x64 CPython 3.11, pytest installed):

```powershell
.venv/Scripts/python.exe -m pytest evaluation/windows_runner/test_portable.py evaluation/windows_runner/test_native.py -q
.venv/Scripts/python.exe evaluation/windows_runner/collect_evidence.py NEW_UNIQUE_RUN_ID
openspec validate board-geometry-foundation --strict
git -c safe.directory=C:/dev/aoi-platform diff --check
```

The collector refuses an existing run directory and runs the existing product
suite, reader harness regressions and runner tests. It does not enable the local
REAL-PCB fixture opt-in. Each native case runs under an independent 20-second
watchdog using the base interpreter, not the venv redirector. Test limits in
[policy.py](policy.py) are synthetic test values, not production defaults.

## Actual evidence, not yet externally reviewed

[review-03](evidence/review-03/environment-command.json): 491 passed, 1 skipped,
17.99 seconds: 370 existing product tests, 23 existing harness tests, 57 portable
runner tests and 41 native cases. The single skip is the existing local fixture
opt-in, not a Windows runner test. Windows reported 10.0 build 26300, AMD64;
CPython 3.11.9 MSC v.1938 AMD64. No claim for other Windows builds/interpreters.
Raw pytest stdout/stderr/XML and per-case output, verification and handle counts
are retained. Earlier review-01/02 evidence is preserved, superseded by review-03.

Native cases cover exit/binary/empty/malformed JSON, exact/+1 stream and combined
budgets, balanced output and flood, timeout, root exit with descendants holding
pipes or no pipes, tree termination, assigned-parent crash, non-inherited Job,
read-only staged input and retained caller handle, process/job memory pressure
with higher-limit controls, and process count rejection. Memory refusal is
reported by the helper with raw nonzero status; runner does not infer a memory
violation from arbitrary exit codes or peak counters.

Setup/resume/read/peek/query/close and cleanup-deadline failure tests use explicit
fault injection around real native execution. Native invalid Job assignment also
rejects before resume. Compatible nested Jobs were exercised; a naturally
incompatible enclosing Job was not reproduced on this host. No reader threads or
pending overlapped I/O exist: polling reads only peeked bytes with a sole reader.
CancelIo failure is therefore not a claimed test; read/peek/close failures are.

Handle counts use explicit unmodified warmups: first pipe/process initialization
caches three OS/runtime handles; first missing-image launch caches seven more.
Second warmup must have zero growth, then the tested operation must have zero
growth. Raw warmup deltas remain visible. Cleanup errors remain failure even if a
best-effort close retry succeeds; an uncertain cleanup is never labeled cleaned.

## Remaining limits / review points

- These tests establish synthetic resource-control evidence, not adapter or parser
  compatibility, and have not yet received external review.
- Native parent-crash evidence covers an already assigned/resumed Job. There is
  still a non-atomic host-death window between suspended CreateProcess and Assign;
  an unexpected host death there can leave an unassigned suspended process. Full
  all-instruction-boundary parent-crash protection is **not proven/complete**.
- Win32 calls on trusted local handles are not hard-real-time preemptible. The
  watchdog detects hangs; it is not evidence of an OS scheduling guarantee.
- Unsupported platform returns typed failure; actual non-Windows runtime and
  incompatible enclosing Job configurations are not native-tested here.
- A permanent kernel close/query failure can leave cleanup unconfirmed. No
  weaker fallback or usable output is returned. No source bridge, backend pin,
  handshake, observation schema or geometry is implemented.

Tasks 1.5/5.2 remain PARTIAL. Next step is review of this transport slice and its
explicit residual host-death window before expanding any adapter semantics.
