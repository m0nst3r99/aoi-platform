"""Independent controlled angular audit; Decimal oracle never calls solver helpers."""
from pathlib import Path
import sys, json, math, hashlib
from decimal import Decimal as D, localcontext
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from test_registration import request, policy  # schema fixtures only, not oracle
from aoi_platform.geometry import registration as reg
HERE = Path(__file__).parent

def oracle(p, q, precision, coefficients=None):
    with localcontext() as ctx:
        ctx.prec = precision
        p = [tuple(D.from_float(v) for v in row) for row in p]
        q = [tuple(D.from_float(v) for v in row) for row in q]
        n = D(len(p))
        pm = tuple(sum(row[k] for row in p)/n for k in (0,1))
        qm = tuple(sum(row[k] for row in q)/n for k in (0,1))
        x = [(a-pm[0],b-pm[1]) for a,b in p]
        y = [(a-qm[0],b-qm[1]) for a,b in q]
        a = sum(u*r+v*s for (u,v),(r,s) in zip(x,y))
        b = sum(u*s-v*r for (u,v),(r,s) in zip(x,y))
        h = (a*a+b*b).sqrt()
        rho = h/(sum(u*u+v*v for u,v in x)*sum(u*u+v*v for u,v in y)).sqrt()
        c,s = a/h,b/h
        optimum = (c,s,qm[0]-c*pm[0]+s*pm[1],qm[1]-s*pm[0]-c*pm[1])
        c,s,tx,ty = optimum if coefficients is None else tuple(D.from_float(v) for v in coefficients)
        distances = [((c*u-s*v+tx-r)**2+(s*u+c*v+ty-z)**2).sqrt() for (u,v),(r,z) in zip(p,q)]
        return optimum, rho, (sum(v*v for v in distances)/n).sqrt(), max(distances)

def main():
    files = ['src/aoi_platform/geometry/registration.py','src/aoi_platform/geometry/_registration_numeric.py','tests/test_registration.py']
    hashes = {}
    for name in files:
        raw=(ROOT/name).read_bytes(); hashes[name]=hashlib.sha256(raw).hexdigest()
        dest=HERE/'snapshot'/name; dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    rows=[]
    for n in (2,3,16,64):
        for target_rho in (1e-8,2e-8,5e-8,1e-7,1e-6):
            scale=.01
            p=tuple((scale*math.cos(2*math.pi*i/n),scale*math.sin(2*math.pi*i/n)) for i in range(n))
            q=tuple((x+target_rho*(.6*x-.8*y),-y+target_rho*(.8*x+.6*y)) for x,y in p)
            req=request(p,q);pol=policy(min_baseline_mm=.001,max_pair_distance_error_mm=.05,max_fit_rms_mm=.05,max_fit_error_mm=.05)
            exact=oracle(p,q,180);low=oracle(p,q,100)
            convergence=max(abs(a-b) for a,b in zip(exact[0]+exact[1:],low[0]+low[1:]))
            assert convergence<D('1e-85')
            out=reg.fit_rigid_registration(req,pol)
            perm=replace(req,fit_declarations=tuple(reversed(req.fit_declarations)),fit_observations=req.fit_observations[1:]+req.fit_observations[:1])
            assert reg.fit_rigid_registration(perm,pol)==out
            row=dict(n=n,target_rho=target_rho,oracle_rho=str(exact[1]),oracle_coefficients=list(map(str,exact[0])),oracle_convergence=str(convergence),permutation_equal=True,
                source_hex=[[v.hex() for v in point] for point in p],target_hex=[[v.hex() for v in point] for point in q])
            if isinstance(out,reg.RegistrationFailure):
                row.update(status='failure',reason=out.diagnostic.reason,field=out.diagnostic.field_path)
            else:
                evaluated=oracle(p,q,180,out.coefficients)
                err=max(abs(D.from_float(v)-z) for v,z in zip(out.coefficients[:2],exact[0][:2]))
                row.update(status='draft',coefficients=[v.hex() for v in out.coefficients],coefficient_error=str(err),reported_rho=out.correlation,correlation_guard=out.correlation_guard,
                    exact_returned_rms=str(evaluated[2]),exact_returned_max=str(evaluated[3]),rms_error=str(abs(D.from_float(out.fit.rms_mm)-evaluated[2])),max_error=str(abs(D.from_float(out.fit.maximum_mm)-evaluated[3])),rms_guard=out.fit.rms_guard_mm,max_guard=out.fit.maximum_guard_mm,
                    false_pass=evaluated[2]>D.from_float(pol.max_fit_rms_mm) or evaluated[3]>D.from_float(pol.max_fit_error_mm),threshold_probes=[])
                for delta in (-4,-1,0,1,4):
                    limit=float(evaluated[2])+delta*out.fit.rms_guard_mm
                    tested=reg.fit_rigid_registration(req,replace(pol,max_fit_rms_mm=limit))
                    passed=isinstance(tested,reg.RegistrationDraft)
                    row['threshold_probes'].append(dict(limit=limit.hex(),guard_multiple=delta,status='draft' if passed else tested.diagnostic.reason,false_pass=passed and evaluated[2]>D.from_float(limit)))
            rows.append(row)
    post={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    assert post==hashes
    report=dict(precision=[100,180],criterion='Existing regression coefficient tolerance 1e-12; not a certified public bound',policy=dict(min_baseline_mm=.001,max_pair_distance_error_mm=.05,max_fit_rms_mm=.05,max_fit_error_mm=.05),hashes_before=hashes,hashes_after=post,rows=rows)
    with (HERE/'results.json').open('x') as f:json.dump(report,f,indent=2)
    drafts=[r for r in rows if r['status']=='draft']
    print(json.dumps(dict(cases=len(rows),drafts=len(drafts),coefficient_counterexamples=sum(D(r['coefficient_error'])>D('1e-12') for r in drafts),max_coefficient_error=str(max(D(r['coefficient_error']) for r in drafts)),false_passes=sum(r['false_pass']+sum(p['false_pass'] for p in r['threshold_probes']) for r in drafts)),indent=2))

if __name__=='__main__':main()
