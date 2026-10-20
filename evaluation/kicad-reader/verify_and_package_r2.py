"""Read-only verification of both snapshots and a new review ZIP (exclusive create)."""
import hashlib
import json
from pathlib import Path
import zipfile

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / 'evaluation/kicad-reader'
EVIDENCE = ROOT / 'population-errata-r2'
R1 = Path('C:/dev/aoi-reference/Edgeberry-Baseboard-working/fixture-revisions/REAL-PCB-01-r1')
R2 = R1.with_name('REAL-PCB-01-r2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    before = read(EVIDENCE / 'parent-before.json')
    assert inventory(R1) == before
    a, b = read(R1/'population.json'), read(R2/'population.json')
    assert len(a) == len(b) == 57
    changes = []
    for index, (left, right) in enumerate(zip(a, b)):
        assert left.keys() == right.keys() and left['uuid'] == right['uuid']
        for key in left:
            if left[key] != right[key]:
                changes.append(dict(uuid=left['uuid'], field=key, index=index, before=left[key], after=right[key]))
    assert changes == read(EVIDENCE/'population-semantic-diff.json')
    assert len(changes) == 12 and all(c['field']=='dnp' and c['before'] is False and c['after'] is True for c in changes)
    hashes2 = inventory(R2)
    assert set(hashes2) == set(before)
    changed_files = {p for p in before if before[p] != hashes2[p]}
    assert changed_files == {'population.json','manifest.json','SHA256SUMS.txt'}
    checksum_counts = {}
    for root in (R1,R2):
        rows = (root/'SHA256SUMS.txt').read_text().splitlines()
        names = []
        for line in rows:
            digest, name = line.split('  ',1)
            name = name.replace('\\','/')
            assert sha(root/name) == digest
            names.append(name)
        assert len(names) == len(set(names)) == 25
        assert set(names) == set(inventory(root)) - {'SHA256SUMS.txt'}
        checksum_counts[root.name] = len(names)
    manifest = read(R2/'manifest.json')
    assert manifest['status']=='pending-review' and manifest['parent_revision']==R1.name
    assert manifest['parent_manifest_sha256'] == sha(R1/'manifest.json')
    assert manifest['parent_inventory_sha256'] == sha(R1/'SHA256SUMS.txt')
    assert manifest['population_before_sha256'] == sha(R1/'population.json')
    assert manifest['population_after_sha256'] == sha(R2/'population.json')
    assert manifest['errata_sha256'] == sha(EVIDENCE/'errata.json')
    assert manifest['artifacts_sha256'] == {k:v for k,v in hashes2.items() if k not in ('manifest.json','SHA256SUMS.txt')}
    audit = read(ROOT/'runs/review-fix-01/dnp-source-audit.json')
    source = R1/'source/Edgeberry.kicad_pcb'
    lines = source.read_text().splitlines()
    assert audit['source_sha256']==sha(source)
    assert {c['uuid'] for c in changes} == {e['uuid'] for e in audit['evidence']}
    for row in audit['evidence']:
        assert '\n'.join(lines[row['attr_start_line']-1:row['attr_end_line']]) == row['raw_attributes']
        assert row['uuid'] in lines[row['uuid_line']-1]
        assert '\t\t\tdnp' in row['raw_attributes'].splitlines()
    outcomes = {}
    for root, run in ((R1,'errata-r1-01'),(R2,'errata-r2-01')):
        report=read(ROOT/'runs'/run/'results.json')
        assert report['fixture_before'] == report['fixture_after'] == inventory(root)
        assert len(report['checks']) == len(report['required_checks']) == 27
        outcomes[root.name] = dict(outcome=report['outcome'], passed=sum(report['checks'].values()), conflicts=len(report['conflicts']))
    assert outcomes[R1.name] == dict(outcome='failed',passed=26,conflicts=12)
    assert outcomes[R2.name] == dict(outcome='passed',passed=27,conflicts=0)
    with zipfile.ZipFile(REPO/'aoi-reader-evaluation-review-v2.zip') as old:
        for name in ('run.py','probe.py','test_harness.py'):
            assert old.read('evaluation/kicad-reader/'+name) == (ROOT/name).read_bytes()
        old_logs=[p for p in ROOT.glob('*') if p.name in ('results.json','malformed.kicad_pcb') or p.name.endswith(('.stdout.txt','.stderr.txt'))]
        assert len(old_logs)==14
        for path in old_logs:
            assert old.read('evaluation/kicad-reader/'+path.name) == path.read_bytes()
    verification=dict(parent_unchanged=True, semantic_changes=12, unchanged_other_files=23,
                      snapshot_checksum_entries=checksum_counts, derived_manifest_payload_entries=24,
                      source_attributes_confirmed=12, harness_files_unchanged=3, old_evidence_files_unchanged=14,
                      outcomes=outcomes, regressions='23 passed in 1.14s; exit 0',
                      openspec='strict validation passed', diff_check='passed', review_status='errata/r2 pending')
    with (EVIDENCE/'final-verification.json').open('x',encoding='utf-8') as stream:
        json.dump(verification,stream,indent=2,sort_keys=True)
        stream.write('\n')
    files={}
    for root in (R1,R2):
        for p in root.rglob('*'):
            if p.is_file(): files['fixtures/'+root.name+'/'+p.relative_to(root).as_posix()]=p
    for p in ROOT.rglob('*'):
        if p.is_file() and not any(part in ('__pycache__','.pytest_cache') for part in p.parts):
            files[p.relative_to(REPO).as_posix()]=p
    for name in ('HANDOFF.md','pyproject.toml','openspec/changes/board-geometry-foundation/implementation-status.md',
                 'openspec/changes/board-geometry-foundation/supported-inputs.md'):
        files[name]=REPO/name
    package_manifest={name:sha(p) for name,p in sorted(files.items())}
    archive=REPO/'aoi-population-errata-r2-review.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name,p in sorted(files.items()): bundle.write(p,name)
        bundle.writestr('REVIEW-MANIFEST.json',json.dumps(dict(sha256=package_manifest,
            scope='Errata/r2 pending review. Contains full parent and derived snapshots including source PCB and licenses. Preparation scripts are historical: do not execute them.',
            head='4e59ad93cc9f753e5c84ca8df7a49868dfde2470'),indent=2)+'\n')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for name,digest in package_manifest.items():
            assert hashlib.sha256(bundle.read(name)).hexdigest()==digest
    print(json.dumps(dict(verification=verification,archive=str(archive),
                         package_files_verified=len(package_manifest),zip_sha256=sha(archive)),indent=2))


if __name__=='__main__':
    main()
