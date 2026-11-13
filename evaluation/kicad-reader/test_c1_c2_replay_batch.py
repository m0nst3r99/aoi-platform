"""Real pinned admission; private gate doubles are explicitly not hash bypasses."""
import json
import os
from pathlib import Path
import pytest
import c1_c2_replay_batch as flow
ROOT=Path(__file__).resolve().parents[2]

@pytest.fixture
def paths():
    source=os.environ.get('AOI_C2_R2_PCB')
    assert source, 'Real PCB required; no fallback'
    result={'pcb':Path(source),'observation':ROOT/'evaluation/windows_runner/evidence/c1-strict-native-01/stdout.bin'}
    for group in ('C1','C2'):
        ev=ROOT/('evaluation/windows_runner/evidence/'+group.lower()+'-boundary-native-01')
        for key,name in [('boundary','stdout.bin'),('report','report.json'),('transport','transport.json')]:result[group+'_'+key]=ev/name
    return result

def failed(result,gate):
    assert isinstance(result,flow.ReplayFailure),result
    assert result.gate==gate
    assert not hasattr(result,'candidates')

def test_real_batch_once_order_provenance_and_oracle(paths,monkeypatch):
    counts={'inventory':0,'candidate':0}; streams=[]
    for name,key in [('inventory_artifacts','inventory'),('build_rectangular_pad_candidates','candidate')]:
        original=getattr(flow,name)
        def wrap(request,*args,_fn=original,_key=key):
            counts[_key]+=1
            if _key=='candidate':
                assert len(request.parents)==2 and len(request.pads)==4
                assert len({p.source_frame for p in request.parents})==1
                assert request.target_frame.origin=='native-board'
            return _fn(request,*args)
        monkeypatch.setattr(flow,name,wrap)
    original=flow.BytesIO
    def track(data):
        stream=original(data);streams.append(stream);return stream
    monkeypatch.setattr(flow,'BytesIO',track)
    before={k:p.read_bytes() for k,p in paths.items()}
    result=flow.replay_batch(paths)
    assert isinstance(result,flow.ReplaySuccess),result
    assert counts=={'inventory':1,'candidate':1}
    assert len(streams)==8 and all(s.closed for s in streams)
    assert len(result.candidates)==4
    assert [c.pad_id for c in result.candidates]==sorted(c.pad_id for c in result.candidates)
    assert {a.declaration.artifact_id:(a.computed_sha256,a.actual_size) for a in result.inventory.inventory.artifacts}=={k:(h,n) for k,h,n in flow.PINS}
    # Independent source-oracle literals, not comparator/candidate-generated expected.
    oracle={
      'e2743daf-d278-4538-a77e-8f62f1b7978c':[(191.64885,-63.76606),(191.64885,-60.26594),(194.04915,-60.26594),(194.04915,-63.76606)],
      '4e53dd71-4be4-4973-9c48-191e7b2e27bb':[(191.64885,-70.26846),(191.64885,-66.76834),(194.04915,-66.76834),(194.04915,-70.26846)],
      '21e4d927-86ab-439d-8b84-9241bc089b89':[(157.15615,-69.57314),(157.15615,-73.07326),(154.75585,-73.07326),(154.75585,-69.57314)],
      'fc38c22a-efcb-4dfc-b42c-80a66f75e1a4':[(157.15615,-63.07074),(157.15615,-66.57086),(154.75585,-66.57086),(154.75585,-63.07074)]}
    for c in result.candidates:
        group=next(g for g,cmp in flow.GROUPS if c.pad_id in cmp.PADS)
        expected_keys={'pcb','observation',group+'_boundary',group+'_report',group+'_transport'}
        assert {r.artifact_id:r.computed_sha256 for r in c.source.provenance.evidence}=={k:h for k,h,n in flow.PINS if k in expected_keys}
        assert not c.published and not c.targeting_authorized
        for i,j in enumerate((3,2,1,0)):
            assert (c.vertices[j].x,c.vertices[j].y)==pytest.approx(oracle[c.pad_id][i],abs=1e-6,rel=0)
    assert before=={k:p.read_bytes() for k,p in paths.items()}
    assert flow.replay_batch(dict(reversed(list(paths.items()))))==result

@pytest.mark.parametrize('key',[k for k,h,n in flow.PINS])
def test_real_hash_failure(paths,tmp_path,monkeypatch,key):
    data=bytearray(paths[key].read_bytes());data[0]^=1
    p=tmp_path/key;p.write_bytes(data);paths[key]=p
    monkeypatch.setattr(flow,'_evaluate_admitted',lambda *a:pytest.fail('hash bypass'))
    failed(flow.replay_batch(paths),'inventory')

@pytest.mark.parametrize('case',['short','over','missing','extra','absent'])
def test_bounded_input(paths,tmp_path,case):
    if case=='extra':paths['extra']=paths['pcb']
    elif case=='absent':paths.pop('pcb')
    else:
        p=tmp_path/'pcb'
        if case!='missing':p.write_bytes(paths['pcb'].read_bytes()[:-1] if case=='short' else paths['pcb'].read_bytes()+b'x')
        paths['pcb']=p
    failed(flow.replay_batch(paths),'input')

@pytest.fixture
def admitted(paths):
    result=flow.replay_batch(paths);assert isinstance(result,flow.ReplaySuccess)
    return {k:p.read_bytes() for k,p in paths.items()},result.inventory

@pytest.mark.parametrize('group',['C1','C2'])
@pytest.mark.parametrize('case',['transport','cleanup','binding','hole','corner','pose'])
def test_private_group_gate_double(admitted,monkeypatch,group,case):
    raw,inventory=admitted
    key=group+('_transport' if case in ('transport','cleanup') else '_report' if case=='binding' else '_boundary')
    if case=='pose':key='observation'
    data=json.loads(raw[key])
    if case=='transport':data['success']=False
    elif case=='cleanup':data['result']['evidence']['active_processes']=1
    elif case=='binding':data['output_hashes']['stdout.bin']='0'*64
    elif case=='hole':data['pads'][0]['contours'][0]['hole_count']=1
    elif case=='corner':data['pads'][0]['contours'][0]['vertices_iu'][0][0]+=2
    else:
        cmp=dict(flow.GROUPS)[group]
        parent=next(f for f in data['footprints'] if f['uuid']==cmp.PARENT)
        parent['pads'][0]['position_mm'][0]+=1
    raw[key]=json.dumps(data).encode();before=dict(raw)
    if case!='pose':monkeypatch.setattr(flow,'build_rectangular_pad_candidates',lambda *a:pytest.fail('candidate called before both gates'))
    gate={'transport':'transport','cleanup':'transport','binding':'binding','hole':'boundary','corner':'boundary','pose':'candidate-boundary'}[case]
    failed(flow._evaluate_admitted(raw,inventory),group+':'+gate)
    assert raw==before

@pytest.mark.parametrize('case',['legacy','schema','candidate'])
def test_private_common_failure_double(admitted,monkeypatch,case):
    raw,inventory=admitted
    if case=='candidate':
        monkeypatch.setattr(flow,'build_rectangular_pad_candidates',lambda *a:None)
        gate='candidate'
    else:
        data=json.loads(raw['observation'])
        if case=='legacy':data.pop('protocol_version')
        else:data['outline']['valid']='true'
        raw['observation']=json.dumps(data).encode();gate='observation-schema'
    failed(flow._evaluate_admitted(raw,inventory),gate)
