"""Pinned real replay tests; deep-gate doubles never claim byte admission."""
import json
import os
from pathlib import Path
from dataclasses import replace
import pytest
import c1_replay_flow as flow

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evaluation/windows_runner/evidence/c1-boundary-native-01'

@pytest.fixture
def paths():
    configured=os.environ.get('AOI_C1_R2_PCB')
    assert configured, 'Set AOI_C1_R2_PCB; no synthetic source fallback'
    return dict(pcb=Path(configured),observation=ROOT/'evaluation/kicad-reader/runs/errata-r2-01/pcbnew.stdout.txt',boundary=EV/'stdout.bin',report=EV/'report.json',transport=EV/'transport.json')

def failure(result,gate):
    assert isinstance(result,flow.ReplayFailure)
    assert result.gate==gate
    assert not hasattr(result,'candidates')

def test_real_inventory_boundaries_candidates(paths,monkeypatch):
    streams=[]
    original=flow.BytesIO
    def track(data):
        stream=original(data);streams.append(stream);return stream
    monkeypatch.setattr(flow,'BytesIO',track)
    before={k:p.read_bytes() for k,p in paths.items()}
    result=flow.replay_c1(paths)
    assert isinstance(result,flow.ReplaySuccess),result
    assert len(streams)==5 and all(s.closed for s in streams)
    assert len(result.candidates)==2
    assert {a.declaration.artifact_id:(a.computed_sha256,a.actual_size) for a in result.inventory.inventory.artifacts}=={k:(h,n) for k,h,n in flow.PINS}
    for c in result.candidates:
        assert not c.published and not c.targeting_authorized
        assert c.association_status=='declaration-consistent'
        assert {r.artifact_id:r.computed_sha256 for r in c.source.provenance.evidence}=={k:h for k,h,n in flow.PINS}
        for i,j in enumerate((3,2,1,0)):
            # Independent accepted C1 source-oracle literals, not flow output.
            expected={
              'e2743daf-d278-4538-a77e-8f62f1b7978c':[(191.64885,-63.76606),(191.64885,-60.26594),(194.04915,-60.26594),(194.04915,-63.76606)],
              '4e53dd71-4be4-4973-9c48-191e7b2e27bb':[(191.64885,-70.26846),(191.64885,-66.76834),(194.04915,-66.76834),(194.04915,-70.26846)]}[c.pad_id][i]
            assert (c.vertices[j].x,c.vertices[j].y)==pytest.approx(expected,abs=1e-6,rel=0)
    assert before=={k:p.read_bytes() for k,p in paths.items()}

@pytest.mark.parametrize('key',['pcb','observation','boundary','report','transport'])
def test_real_hash_gate_blocks_before_deep_gates(paths,tmp_path,monkeypatch,key):
    data=bytearray(paths[key].read_bytes());data[0]^=1
    bad=tmp_path/key;bad.write_bytes(data);paths[key]=bad
    def forbidden(*args):pytest.fail('Hash failure reached post-admission gates')
    monkeypatch.setattr(flow,'_evaluate_admitted',forbidden)
    failure(flow.replay_c1(paths),'inventory')

@pytest.mark.parametrize('case',['missing','size'])
def test_input_failure(paths,tmp_path,case):
    bad=tmp_path/'pcb'
    if case=='size':bad.write_bytes(b'x')
    paths['pcb']=bad
    failure(flow.replay_c1(paths),'input')

@pytest.fixture
def admitted_double(paths):
    # Real positive inventory first; mutations below are ONLY private gate doubles.
    result=flow.replay_c1(paths)
    assert isinstance(result,flow.ReplaySuccess),result
    return {k:p.read_bytes() for k,p in paths.items()},result.inventory

@pytest.mark.parametrize('case,gate',[
 ('transport','transport'),('exit','transport'),('cleanup','transport'),('active','transport'),('eof','transport'),('staging','transport'),
 ('output_hash','binding'),('source_hash','binding'),('build','binding'),('legacy_upgrade','binding'),
 ('open','boundary'),('hole','boundary'),('corner','boundary'),('parent','observation'),('candidate_mismatch','candidate-boundary'),('json','transport')])
def test_private_post_admission_gate_double(admitted_double,case,gate):
    raw,inventory=admitted_double
    before=dict(raw)
    key='transport'
    if case in ('staging','output_hash'):key='report'
    if case in ('source_hash','build','legacy_upgrade','parent','candidate_mismatch'):key='observation'
    if case in ('open','hole','corner'):key='boundary'
    data=json.loads(raw[key])
    if case=='transport':data['success']=False
    elif case=='exit':data['result']['evidence']['root_exit']=1
    elif case=='cleanup':data['result']['evidence']['cleanup_state']='unknown'
    elif case=='active':data['result']['evidence']['active_processes']=1
    elif case=='eof':data['result']['evidence']['stdout_eof']=False
    elif case=='staging':data['staging_removed']=False
    elif case=='output_hash':data['output_hashes']['stdout.bin']='0'*64
    elif case=='source_hash':data['input_sha256']='0'*64
    elif case=='build':data['build']='wrong'
    elif case=='legacy_upgrade':data['protocol_version']=2
    elif case=='open':data['pads'][0]['contours'][0]['closed']=False
    elif case=='hole':data['pads'][0]['contours'][0]['hole_count']=1
    elif case=='corner':data['pads'][0]['contours'][0]['vertices_iu'][0][0]+=2
    elif case in ('parent','candidate_mismatch'):
        f=next(f for f in data['footprints'] if f['uuid']==flow.PARENT)
        if case=='parent':f['layer']='B.Cu'
        else:f['pads'][0]['position_mm'][0]+=1
    raw[key]=b'{' if case=='json' else json.dumps(data).encode()
    changed=dict(raw)
    failure(flow._evaluate_admitted(raw,inventory),gate)
    assert raw==changed
    assert flow.PINS==tuple(flow.PINS)  # No hash policy override is exposed.
    assert before[key]!=raw[key]

def test_candidate_api_failure_double(admitted_double,monkeypatch):
    raw,inventory=admitted_double
    monkeypatch.setattr(flow,'build_rectangular_pad_candidates',lambda request:None)
    failure(flow._evaluate_admitted(raw,inventory),'candidate')
