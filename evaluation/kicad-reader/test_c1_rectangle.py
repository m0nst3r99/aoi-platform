"""C1 portable candidate math; historical observation, not native boundary verification.
Inventory is an explicit trusted fixture double, not a rerun of PCB byte admission.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json
import pytest
from aoi_platform.inventory import ArtifactDeclaration, ArtifactObservation, ArtifactInventory, InventoryManifest, InventorySuccess
from aoi_platform.geometry.reports import ValidationReport
from aoi_platform.geometry.models import Frame, FrameKind, Unit, AxisDirection as Axis, Point2
from aoi_platform.geometry.transforms import Transform2, TransformKind
from aoi_platform.pad_candidates import (SyntheticPadPolicy, EvidenceReference, PadProvenance, PadParent, SourcePad, PadRectangle, PadCandidateRequest, PadBatchSuccess, build_rectangular_pad_candidates)

HERE=Path(__file__).resolve().parent
RAW=HERE/'runs/errata-r2-01/pcbnew.stdout.txt'
SOURCE_HASH='67c71f525eab73d2bde26eeb9f683cd2ac80a75ed6a43938cb553774a5fe33d0'
RAW_HASH='10f57cac75d8d998e450cf91d2aaf748e289fd512f1c1568b5ca9298a9494b9c'
PARENT='00000000-0000-0000-0000-00005bd482c8'
# Literal independent values from C1-ORACLE.md; never generated from observation.
ORACLE={
 'e2743daf-d278-4538-a77e-8f62f1b7978c': ((191.64885,-63.76606),(191.64885,-60.26594),(194.04915,-60.26594),(194.04915,-63.76606)),
 '4e53dd71-4be4-4973-9c48-191e7b2e27bb': ((191.64885,-70.26846),(191.64885,-66.76834),(194.04915,-66.76834),(194.04915,-70.26846)),
}
CORRESPONDENCE=(3,2,1,0)  # N(q0..q3) corresponds to candidate offsets q3..q0.
POLICY=SyntheticPadPolicy('synthetic-rect-pad-candidate','1',4096,4096,1024,256,1024,16,32768,8388608,128,4096,524288,1000000.,.000001,1000000.,360000.,1e-12,0.,1e-6)


def build_case():
 raw=RAW.read_bytes(); assert sha256(raw).hexdigest()==RAW_HASH
 data=json.loads(raw); before=json.dumps(data,sort_keys=True)
 assert 'protocol_version' not in data  # Do not upgrade or pass legacy to strict-v2.
 assert data['input_sha256']==SOURCE_HASH
 f=next(f for f in data['footprints'] if f['uuid']==PARENT)
 assert f['layer']=='F.Cu' and {p['uuid'] for p in f['pads']}==set(ORACLE)
 # Trusted test double supplies provenance contract only; no claim about actual source size.
 d=ArtifactDeclaration('pcb','kicad_pcb','fixture-double',SOURCE_HASH)
 o=ArtifactDeclaration('observation','supporting','saved-observation',RAW_HASH,reference_only=True)
 inv=InventorySuccess(ArtifactInventory(InventoryManifest('geometry',(d,o),'REAL-PCB-01-r2','accepted-snapshot'),
     (ArtifactObservation(d,1,True,1,SOURCE_HASH),ArtifactObservation(o,len(raw),True,len(raw),RAW_HASH))),ValidationReport('fixture-double','test-only',(),(('scope','artifact-bytes-only'),)))
 s=Frame('normalized',FrameKind.SOURCE,Unit.MM,'declared-C1-datum',Axis.RIGHT,Axis.UP,'c1-unpublished')
 t=Frame('P',FrameKind.PCB,Unit.MM,'declared-C1-datum',Axis.RIGHT,Axis.UP,'c1-unpublished')
 mapping=Transform2('declared-zero-translation',s,t,((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),TransformKind.RIGID)
 refs=(EvidenceReference('pcb',SOURCE_HASH,'source declarations C1 lines 88-354'),EvidenceReference('observation',RAW_HASH,'N(x,y)=(x,-y); world angle retained; correspondence 3,2,1,0'))
 prov=PadProvenance('pcb','fixture-double',SOURCE_HASH,PARENT,'accepted-snapshot','REAL-PCB-01-r2','C1-portable-evaluation','1',refs)
 parent=PadParent('C1',PARENT,'pcb',s,'board-source','top',mapping,refs,prov)
 pads=[]
 for p in f['pads']:
  assert p['shape']==1 and p['attribute']==1 and p['drill_mm']==[0,0]
  assert set(p['layers'])=={'F.Cu','F.Mask','F.Paste'}
  x,y=p['position_mm']  # Already world; do not add footprint pose or local offsets.
  pads.append(SourcePad(p['uuid'],'C1',p['uuid'],PARENT,'pcb',s,p['number'],'top',('F.Cu',),'smd',None,
      PadRectangle(Point2(x,-y,s),*p['size_mm'],p['angle_deg']),replace(prov,source_entity_id=p['uuid'])))
 result=build_rectangular_pad_candidates(PadCandidateRequest('rect-pad-candidate-v1',POLICY,'C1-board','c1-unpublished',t,inv,(parent,),tuple(pads)))
 assert isinstance(result,PadBatchSuccess),result
 assert json.dumps(data,sort_keys=True)==before and RAW.read_bytes()==raw
 return result


@pytest.mark.parametrize('uid',tuple(ORACLE))
def test_c1_four_corresponding_corners(uid):
 result=build_case(); assert len(result.candidates)==2
 c=next(c for c in result.candidates if c.pad_id==uid)
 assert len(c.vertices)==4
 for source_index,candidate_index in enumerate(CORRESPONDENCE):
  v=c.vertices[candidate_index]
  assert (v.x,v.y)==pytest.approx(ORACLE[uid][source_index],abs=1e-6,rel=0)
 assert c.source.rectangle.angle_deg==90.0
 assert not c.published and not c.targeting_authorized
 assert c.association_status=='declaration-consistent'
 assert c.parent.source_to_p.matrix==((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))


def test_reflection_winding_is_correspondence_not_geometry_error():
 def cross(points):
  a,b,c=points[:3]
  return (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
 for c in build_case().candidates:
  actual=[(p.x,p.y) for p in c.vertices]
  assert cross(actual)>0
  assert cross(ORACLE[c.pad_id])<0
  assert cross([actual[i] for i in CORRESPONDENCE])<0
