"""Fixture-specific source excerpt audit, NOT a KiCad/S-expression parser.

Requires the exact accepted source hash and its observed tab-indented layout.
No fallback parsing or general format support. Keeps line-numbered raw attributes.
"""
import hashlib
import json
from pathlib import Path
import sys

source, population_file, report_file, output = map(Path, sys.argv[1:])
raw = source.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
assert digest == '67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0'
lines = raw.decode('utf-8').splitlines()
population = {p['uuid']: p for p in json.loads(population_file.read_text(encoding='utf-8-sig'))}
report = json.loads(report_file.read_text(encoding='utf-8'))
conflicts = report['conflicts']
assert len(conflicts) == 12 and all(c['field'] == 'dnp' for c in conflicts)
evidence = []
for conflict in sorted(conflicts, key=lambda c: c['uuid']):
    uuid = conflict['uuid']
    matches = [i for i, line in enumerate(lines) if line == f'\t\t(uuid "{uuid}")']
    assert len(matches) == 1
    index = matches[0]
    start = max(i for i in range(index) if lines[i].startswith('\t(footprint '))
    end = next(i for i in range(index + 1, len(lines)) if lines[i] == '\t)')
    attrs = [i for i in range(index, end) if lines[i].startswith('\t\t(attr ')]
    assert len(attrs) == 1
    first = attrs[0]
    last = first if lines[first].endswith(')') else next(i for i in range(first + 1, end) if lines[i] == '\t\t)')
    excerpt = lines[first:last + 1]
    # Exact fixture layout, dnp is its own indented line in all 12 cases.
    has_dnp = '\t\t\tdnp' in excerpt or 'dnp)' in excerpt[0].split()
    assert has_dnp and conflict['observed'] is True and conflict['declared'] is False
    evidence.append(dict(uuid=uuid, source_sha256=digest,
                         source_footprint_line=start + 1, uuid_line=index + 1,
                         attr_start_line=first + 1, attr_end_line=last + 1,
                         raw_attributes='\n'.join(excerpt), source_dnp=has_dnp,
                         native_dnp=conflict['observed'], population_dnp=population[uuid]['dnp']))
result = dict(source=str(source), source_sha256=digest,
              population_sha256=hashlib.sha256(population_file.read_bytes()).hexdigest(),
              native_report_sha256=hashlib.sha256(report_file.read_bytes()).hexdigest(),
              scope='exact-hash fixture excerpt audit only', count=len(evidence), evidence=evidence)
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write('\n')
print('Confirmed source DNP attributes for all 12 UUIDs; fixture unchanged.')
