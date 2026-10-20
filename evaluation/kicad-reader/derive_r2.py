"""One-time, explicit fixture metadata derivation; not product publication."""
from datetime import datetime, timezone
import copy
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
PARENT = Path('C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1')
TARGET = PARENT.with_name('REAL-PCB-01-r2')
EVIDENCE = ROOT / 'population-errata-r2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    assert not TARGET.exists() and not EVIDENCE.exists(), 'New directories required'
    before = inventory(PARENT)
    previous = json.loads((ROOT / 'runs/review-fix-01/results.json').read_text())
    assert before == {k.replace('\\', '/'): v for k, v in previous['fixture_after'].items()}
    for line in (PARENT / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert before[name.replace('\\', '/')] == digest
    audit_file = ROOT / 'runs/review-fix-01/dnp-source-audit.json'
    audit = json.loads(audit_file.read_text())
    assert audit['source_sha256'] == before['source/Edgeberry.kicad_pcb']
    assert audit['population_sha256'] == before['population.json']
    assert audit['native_report_sha256'] == sha(ROOT / 'runs/review-fix-01/results.json')
    entries = audit['evidence']
    ids = {e['uuid'] for e in entries}
    assert len(entries) == len(ids) == 12
    original = json.loads((PARENT / 'population.json').read_text(encoding='utf-8-sig'))
    corrected = copy.deepcopy(original)
    assert len({p['uuid'] for p in original}) == len(original)
    edits = []
    for index, row in enumerate(corrected):
        if row['uuid'] in ids:
            assert row['dnp'] is False
            row['dnp'] = True
            edits.append(dict(uuid=row['uuid'], field='dnp', index=index, before=False, after=True))
    assert len(edits) == 12
    for a, b in zip(original, corrected):
        changes = [k for k in a if a[k] != b[k]]
        assert changes == (['dnp'] if a['uuid'] in ids else [])
    EVIDENCE.mkdir()
    save(EVIDENCE / 'parent-before.json', before)
    save(EVIDENCE / 'population-semantic-diff.json', edits)
    errata = dict(id='REAL-PCB-01-population-DNP-errata-01', parent_revision='REAL-PCB-01-r1',
                  derived_revision='REAL-PCB-01-r2', status='pending-review',
                  reason='Correct descriptive fixture metadata only; no PCB or assembly decision change',
                  source_sha256=audit['source_sha256'], population_before_sha256=audit['population_sha256'],
                  native_report_sha256=audit['native_report_sha256'], audit_sha256=sha(audit_file),
                  review_scope='User reports v2 ZIP harness review accepted: 23/23 regression, 44/44 manifest hashes, 14 old logs unchanged. Reviewer did not have complete source PCB or rerun KiCad. Errata/r2 not yet reviewed.',
                  evidence=entries)
    save(EVIDENCE / 'errata.json', errata)
    shutil.copytree(PARENT, TARGET)
    (TARGET / 'population.json').write_text(json.dumps(corrected, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    payload = {k: v for k, v in inventory(TARGET).items() if k not in ('manifest.json', 'SHA256SUMS.txt')}
    parent_manifest = json.loads((PARENT / 'manifest.json').read_text(encoding='utf-8-sig'))
    manifest = dict(fixture_id='REAL-PCB-01', fixture_revision='REAL-PCB-01-r2',
                    created_utc=datetime.now(timezone.utc).isoformat(), status='pending-review',
                    parent_revision='REAL-PCB-01-r1', parent_snapshot=str(PARENT),
                    parent_manifest_sha256=before['manifest.json'], parent_inventory_sha256=before['SHA256SUMS.txt'],
                    upstream_commit_declared_by_user=parent_manifest['upstream_commit_declared_by_user'],
                    upstream_equivalence_verified=False,
                    reason=errata['reason'], changes=edits,
                    population_before_sha256=before['population.json'], population_after_sha256=sha(TARGET / 'population.json'),
                    errata_id=errata['id'], errata_sha256=sha(EVIDENCE / 'errata.json'),
                    source_audit_sha256=sha(audit_file), source_sha256=audit['source_sha256'],
                    artifacts_sha256=payload,
                    inventory_scope='All files except manifest.json and SHA256SUMS.txt; SHA256SUMS includes manifest, excludes itself to avoid recursive hashes',
                    provenance='All payload bytes except 12 population dnp values inherited from r1. Export commands/settings are historical r1 evidence identified by parent manifest hash; no exports rerun.',
                    review_scope=errata['review_scope'],
                    acceptance='No acceptance or attestation inherited from parent; not published into application')
    (TARGET / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    hashes = {k: v for k, v in inventory(TARGET).items() if k != 'SHA256SUMS.txt'}
    (TARGET / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(hashes.items())), encoding='utf-8')
    after = inventory(TARGET)
    differences = [k for k in before if before[k] != after[k]]
    assert set(differences) == {'population.json', 'manifest.json', 'SHA256SUMS.txt'}
    assert inventory(PARENT) == before
    assert all(after[k] == v for k, v in manifest['artifacts_sha256'].items())
    for line in (TARGET / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert after[name] == digest
    save(EVIDENCE / 'derivation-verification.json', dict(parent_unchanged=True,
         semantic_diff_count=len(edits), changed_files=differences,
         unchanged_payload_count=len(before)-len(differences), parent=before, derived=after,
         manifest_payload_hashes_verified=len(payload), checksum_entries_verified=len(hashes)))
    print('Created r2: exactly 12 semantic dnp corrections; 23 other files byte-identical; r1 unchanged.')


if __name__ == '__main__':
    main()
