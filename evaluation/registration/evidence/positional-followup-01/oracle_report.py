"""Numerical report from independent direct-centroid Decimal oracle."""
from pathlib import Path
import sys
import json
import math
from decimal import Decimal as D, localcontext

root = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(root/'src'), str(root/'tests')]
from test_registration_position import request, policy, oracle, supported, assess, check_decimal
from aoi_platform.geometry import registration as reg

rows = []
for n in (2,3,16,64):
    for rho in (1e-8,2e-8,5e-8,1e-7,1e-6):
        source = tuple((.01*math.cos(2*math.pi*i/n), .01*math.sin(2*math.pi*i/n)) for i in range(n))
        target = tuple((x+rho*(.6*x-.8*y), -y+rho*(.8*x+.6*y)) for x,y in source)
        exact = oracle(request(source,target),180)[0]
        corners = ((-150.,-100.), (150.,100.))
        with localcontext() as context:
            context.prec = 180
            c,s,tx,ty = exact
            reference = tuple((float(c*D(x)-s*D(y)+tx),float(s*D(x)+c*D(y)+ty)) for x,y in corners)
        req = supported(request(source,target,corners,reference))
        out = assess(req, policy(min_baseline_mm=.001,max_fit_rms_mm=.05,max_fit_error_mm=.05))
        row = dict(n=n, target_rho=rho, source_hex=[[v.hex() for v in p] for p in source],
            target_hex=[[v.hex() for v in p] for p in target], checkpoint_hex=[[v.hex() for v in p] for p in reference])
        if type(out) is reg.RegistrationFailure:
            row.update(status='failure',reason=out.diagnostic.reason)
        else:
            check_decimal(req,out)
            values = oracle(req,180,out.registration.coefficients,checkpoints=True)
            row.update(status=out.numerical_assessment.value,physical=out.physical_accuracy.value,
                coefficients_hex=[v.hex() for v in out.registration.coefficients],
                coefficient_error=str(max(abs(D.from_float(a)-b) for a,b in zip(out.registration.coefficients[:2],exact[:2]))),
                max_roi_residual_mm=str(values[3]), fit_rms_mm=out.registration.fit.rms_mm,
                max_residual_rounding_error_mm=str(max(abs(D.from_float(a.norm_mm)-b) for a,b in zip(out.registration.checkpoints.records,values[1]))))
        rows.append(row)
path = Path(__file__).with_name('oracle-results.json')
with path.open('x') as output:
    json.dump(rows,output,indent=2)
accepted = [r for r in rows if r['status']=='PASS']
print('cases',len(rows),'numerical PASS',len(accepted),'ambiguous rejection',len(rows)-len(accepted))
print('maximum ROI residual mm',max(D(r['max_roi_residual_mm']) for r in accepted))
print('maximum coefficient error',max(D(r['coefficient_error']) for r in accepted))
print('maximum residual rounding error mm',max(D(r['max_residual_rounding_error_mm']) for r in accepted))
