"""Reconstructable independent numerical report; invoke from repository root.

Uses test-authored Decimal equations at 100/160 digits. No expected values are
obtained from production centering, covariance, guards or residual helpers.
"""
import json
import platform
import sys
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "tests"))
sys.path.insert(0, str(Path.cwd() / "src"))
from test_registration import request, policy, oracle, assert_oracle
from aoi_platform.geometry import registration as reg

cases = []
points = ((-10.,-10.),(-10.,10.),(10.,-10.),(10.,10.))
cases.append(("noisy-rational",request(points,tuple((x*1025/1024+5,y*1025/1024+7) for x,y in points)),policy()))
points = ((2.**20-1,0.),(2.**20-1+2.**-10,0.))
cases.append(("large-offset-small-baseline",request(points,tuple((x,y+1) for x,y in points)),policy(min_baseline_mm=2.**-11)))
for case in range(12):
    c,s = ((1.,0.),(0.,1.),(0.6,0.8))[case%3]
    offset = (0.,2.**17,-2.**18)[case//4]
    points = tuple((offset+x,y) for x,y in ((0.,0.),(21.,2.),(-3.,31.),(22.,29.)))
    target = tuple((c*x-s*y+5+2.**-12*(i%2),s*x+c*y+7-2.**-12*(i//2)) for i,(x,y) in enumerate(points))
    cases.append((f"grid-{case}",request(points,target),policy()))

rows = []
for name,req,pol in cases:
    draft = reg.fit_rigid_registration(req,pol)
    assert_oracle(req,pol,draft)
    a,b = oracle(req,100,draft.coefficients),oracle(req,160,draft.coefficients)
    rows.append({"case":name,"coefficients":draft.coefficients,"correlation":draft.correlation,
        "rms_mm":draft.fit.rms_mm,"maximum_mm":draft.fit.maximum_mm,
        "oracle_rms_100":str(a[2]),"oracle_rms_160":str(b[2]),
        "oracle_precision_delta":str(abs(a[2]-b[2])),
        "rms_error":str(abs(D.from_float(draft.fit.rms_mm)-b[2])),
        "rms_guard":draft.fit.rms_guard_mm,"maximum_error":str(abs(D.from_float(draft.fit.maximum_mm)-b[3])),
        "maximum_guard":draft.fit.maximum_guard_mm,
        "oracle_rms_within_policy":b[2] <= D.from_float(pol.max_fit_rms_mm),
        "oracle_maximum_within_policy":b[3] <= D.from_float(pol.max_fit_error_mm)})
print(json.dumps({"python":sys.version,"platform":platform.platform(),"cases":rows},indent=2))
