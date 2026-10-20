# REAL-PCB-01 population DNP errata / r2 (pending review)

Correct descriptive fixture metadata only; no PCB or assembly decision change. No PCB, exports or assembly classification decisions changed.

User reports v2 ZIP harness review accepted: 23/23 regression, 44/44 manifest hashes, 14 old logs unchanged. Reviewer did not have complete source PCB or rerun KiCad. Errata/r2 not yet reviewed.

Source SHA-256: `67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0`.
Population r1 SHA-256: `7f8cd8e3355ad933007b85a8c92e84998ef1a813be037a8c6f7265556f602a7d`.
Population r2 SHA-256: `002b6c2fb744815ad4da5d08c08880d77ed9b7c83ddb07d36a258c7d0304837d`.
Native report SHA-256: `0b016b041c607db13fb7a70e5affdd1066bfb688a5b586ed7ecd8e4516c69161`.
Audit SHA-256: `5168fed22729ce3f0dce8ab8f487291eee182d1721f1d8c743248879514c29df`.

[Machine-readable errata](errata.json) retains full raw attribute excerpts and all hashes. [Semantic diff](population-semantic-diff.json) and [derivation verification](derivation-verification.json) record the exact edits and byte identities. The original [audit](../runs/review-fix-01/dnp-source-audit.json) is unchanged.

| UUID | r1 ledger DNP | Source/API DNP | Source attr lines |
| --- | --- | --- | --- |
| 110cdf80-ce50-49b4-8323-15cc6e2805de | false | true / true | 13029-13031 |
| 18e8e642-d122-425a-b1c4-4622a1417921 | false | true / true | 3631-3633 |
| 683bda97-6bb0-4314-b236-b92ef02b473b | false | true / true | 5902-5904 |
| 72e2cb3c-84a9-4e35-a2de-1bf710904a82 | false | true / true | 6066-6068 |
| 918b7da7-057f-4892-a244-8576d15a69fb | false | true / true | 6390-6392 |
| 91cb5445-26f3-405b-8e77-03a53e85c2c2 | false | true / true | 6739-6741 |
| 973c81e6-7e5c-4c9c-8b29-3ba4ce3dc8a3 | false | true / true | 7280-7282 |
| c26fea9b-ce24-49d8-9ed2-40dab0eda8f2 | false | true / true | 7932-7934 |
| c30af8cd-6c66-4c4c-83ed-796f98a35f38 | false | true / true | 8137-8139 |
| c896bb5f-b2ac-48fc-95b6-c8b25217b922 | false | true / true | 8267-8269 |
| dcd0819f-f417-4d32-aecf-843f6f08bfa4 | false | true / true | 9375-9377 |
| ff618834-9f37-479d-896c-eddeb1f1df65 | false | true / true | 12342-12344 |

All twelve source attribute blocks contain board_only, exclude_from_pos_files, exclude_from_bom, allow_missing_courtyard and multiline dnp. Corrections do not change eligibility, exclusions or fiducial flags. Source and export hashes remain identical to r1.

r2 manifest declares parent revision/hashes, exact changes, payload inventory and pending-review status. Its checksum file covers 25 files including manifest and excludes itself; manifest payload inventory covers 24 files excluding manifest/checksum (avoids recursive hashes). Of 26 snapshot files, only population, manifest and checksum differ; 23 are byte-identical.

Local checks: r1 FAIL 26/27 (12 population conflicts); r2 PASS 27/27 (zero conflicts). Harness code/checks unchanged. Portable regressions 23 passed in 1.14s, exit 0. All source/audit evidence is supplied for new review; metadata consistency does not establish parser compatibility.

Historical inaccurate descriptions: r1 population.json remains frozen with 12 false DNP entries; r1 manifest/previous preparation summaries are historical, not corrected in place. Repository supported-inputs and handoff now link this errata. Initial evaluation README representative-only audit statement is superseded by the full 12-UUID audit. r1 acceptance and v2 harness acceptance do not accept r2.

No full pytest rerun: no shared product code changed. No checkbox, allowlist, application publication, commit or push.
