"""Portable Python integration; requires explicitly supplied REAL-PCB-01-r2 PCB.
No native execution or strict-v2 upgrade. This file is run explicitly, not default tests/.
"""
import os
import json
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import pytest
from types import SimpleNamespace
from aoi_platform.pad_candidates import SyntheticPadPolicy
from observation_schema import schema
from aoi_platform.inventory import ArtifactDeclaration, InventoryManifest, InventoryLimits, InventorySuccess, inventory_artifacts
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection as Axis, Point2
from aoi_platform.geometry.transforms import Transform2, TransformKind
from aoi_platform.pad_candidates import EvidenceReference, PadProvenance, PadParent, SourcePad, PadRectangle, PadCandidateRequest, PadBatchSuccess, build_rectangular_pad_candidates



# Literal source-derived corners from C2-ORACLE.md; not generated from observation.
oracle=SimpleNamespace(
 RAW=Path(__file__).resolve().parents[1]/'windows_runner/evidence/c1-strict-native-01/stdout.bin',
 RAW_HASH='cd3734ece758d2611b44dc89cec2c88e439ba2d5585024d484671645ed7725b9',
 SOURCE_HASH='67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0',
 PARENT='00000000-0000-0000-0000-00005bd482e1',
 ORACLE={
  '21e4d927-86ab-439d-8b84-9241bc089b89':((157.15615,-69.57314),(157.15615,-73.07326),(154.75585,-73.07326),(154.75585,-69.57314)),
  'fc38c22a-efcb-4dfc-b42c-80a66f75e1a4':((157.15615,-63.07074),(157.15615,-66.57086),(154.75585,-66.57086),(154.75585,-63.07074)),
 },
 CORRESPONDENCE=(3,2,1,0),
 POLICY=SyntheticPadPolicy('synthetic-rect-pad-candidate','1',4096,4096,1024,256,1024,16,32768,8388608,128,4096,524288,1000000.,.000001,1000000.,360000.,1e-12,0.,1e-6),
)

def test_c2_real_inventory_and_eight_corners():
 configured=os.environ.get('AOI_C2_R2_PCB')
 assert configured, 'SOURCE_MISSING: set AOI_C2_R2_PCB to the explicit r2 source PCB; no fallback'
 source=Path(configured)
 assert source.is_absolute() and source.is_file(), f'SOURCE_MISSING: {source}'
 assert oracle.RAW.is_file(), f'SOURCE_MISSING: {oracle.RAW}'
 size=source.stat().st_size
 assert 0<size<=2*1024**2, 'SOURCE_SIZE: outside explicit test budget'
 raw=oracle.RAW.read_bytes()
 assert sha256(raw).hexdigest()==oracle.RAW_HASH, 'SOURCE_CONFLICT: observation hash'
 declarations=(ArtifactDeclaration('pcb','kicad_pcb','r2-source',oracle.SOURCE_HASH,size),
  ArtifactDeclaration('observation','supporting','saved-observation',oracle.RAW_HASH,len(raw),reference_only=True))
 streams=[]
 def opened(path):
  stream=path.open('rb');streams.append(stream);return stream
 inventory=inventory_artifacts(InventoryManifest('geometry',declarations,'REAL-PCB-01-r2','accepted-snapshot'),
  {'r2-source':lambda:opened(source),'saved-observation':lambda:opened(oracle.RAW)},
  InventoryLimits('c2-real-inventory-test-v1',2,2*1024**2,4*1024**2,65536))
 assert isinstance(inventory,InventorySuccess), inventory
 assert len(streams)==2 and all(s.closed for s in streams)
 admitted={a.declaration.artifact_id:a for a in inventory.inventory.artifacts}
 for key,wanted_size,wanted_hash in [('pcb',size,oracle.SOURCE_HASH),('observation',len(raw),oracle.RAW_HASH)]:
  item=admitted[key]
  assert item.eof and item.bytes_read==item.actual_size==item.declaration.declared_size==wanted_size
  assert item.computed_sha256==item.declaration.declared_sha256==wanted_hash
 assert admitted['pcb'].actual_size==912379
 data=json.loads(raw); before=json.dumps(data,sort_keys=True)
 assert data['protocol_version']==2  # Already-v2 saved bytes; no legacy upgrade.
 schema(data)
 assert data['build']=='10.0.7'
 assert data['input_sha256']==admitted['pcb'].computed_sha256
 parents=[f for f in data['footprints'] if f['uuid']==oracle.PARENT]
 assert len(parents)==1
 footprint=parents[0]
 assert len(footprint['pads'])==2 and footprint['angle_deg']==-90
 assert footprint['layer']=='F.Cu' and {p['uuid'] for p in footprint['pads']}==set(oracle.ORACLE)
 s=Frame('normalized',FrameKind.SOURCE,Unit.MM,'declared-C2-datum',Axis.RIGHT,Axis.UP,'c2-unpublished')
 t=Frame('P',FrameKind.PCB,Unit.MM,'declared-C2-datum',Axis.RIGHT,Axis.UP,'c2-unpublished')
 transform=Transform2('declared-zero-translation',s,t,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
 refs=(EvidenceReference('pcb',oracle.SOURCE_HASH,'C2 source declarations'),EvidenceReference('observation',oracle.RAW_HASH,'world coordinates; N(x,y)=(x,-y); correspondence 3,2,1,0'))
 prov=PadProvenance('pcb','r2-source',oracle.SOURCE_HASH,oracle.PARENT,'accepted-snapshot','REAL-PCB-01-r2','C2-real-inventory-evaluation','1',refs)
 parent=PadParent('C2',oracle.PARENT,'pcb',s,'board-source','top',transform,refs,prov)
 pads=[]
 for p in footprint['pads']:
  assert p['shape']==1 and p['attribute']==1 and p['drill_mm']==[0,0]
  assert set(p['layers'])=={'F.Cu','F.Mask','F.Paste'}
  assert p['angle_deg']==270
  x,y=p['position_mm']  # Already world: never apply footprint placement again.
  pads.append(SourcePad(p['uuid'],'C2',p['uuid'],oracle.PARENT,'pcb',s,p['number'],'top',('F.Cu',),'smd',None,
   PadRectangle(Point2(x,-y,s),*p['size_mm'],p['angle_deg']),replace(prov,source_entity_id=p['uuid'])))
 result=build_rectangular_pad_candidates(PadCandidateRequest('rect-pad-candidate-v1',oracle.POLICY,'C2-board','c2-unpublished',t,inventory,(parent,),tuple(pads)))
 assert isinstance(result,PadBatchSuccess),result
 assert len(result.candidates)==2
 assert {c.pad_id for c in result.candidates}==set(oracle.ORACLE)
 for c in result.candidates:
  assert len(c.vertices)==4
  for i,j in enumerate(oracle.CORRESPONDENCE):
   assert (c.vertices[j].x,c.vertices[j].y)==pytest.approx(oracle.ORACLE[c.pad_id][i],abs=1e-6,rel=0)
  assert c.source.provenance==replace(prov,source_entity_id=c.pad_id)
  assert c.parent.provenance==prov
  assert c.source.provenance.evidence[1].computed_sha256==admitted['observation'].computed_sha256
  assert c.association_status=='declaration-consistent'
  assert not c.published and not c.targeting_authorized
 assert json.dumps(data,sort_keys=True)==before and oracle.RAW.read_bytes()==raw
 assert source.stat().st_size==size and sha256(source.read_bytes()).hexdigest()==oracle.SOURCE_HASH
 print(json.dumps({'pcb_bytes':size,'observation_bytes':len(raw),'pcb_sha256':admitted['pcb'].computed_sha256,
  'observation_sha256':admitted['observation'].computed_sha256,'corners_checked':8,'streams_closed':True}))
