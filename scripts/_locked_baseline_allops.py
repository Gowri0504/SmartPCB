import json, os
import numpy as np
ROOT = os.getcwd()

def bbox_iou(a,b):
    ax1,ay1,ax2,ay2=a; bx1,by1,bx2,by2=b
    ix1,iy1=max(ax1,bx1),max(ay1,by1); ix2,iy2=min(ax2,bx2),min(ay2,by2)
    iw,ih=max(0.,ix2-ix1),max(0.,iy2-iy1); inter=iw*ih
    if inter<=0: return 0.0
    return inter/(max(0.,ax2-ax1)*max(0.,ay2-ay1)+max(0.,bx2-bx1)*max(0.,by2-by1)-inter+1e-12)

def ap(tp, fp, n):
    if n<=0: return None
    tp=np.asarray(tp,float); fp=np.asarray(fp,float)
    ctp=np.cumsum(tp); cfp=np.cumsum(fp); rec=ctp/n; prec=ctp/np.maximum(ctp+cfp,1e-9)
    mr=np.concatenate(([0.],rec,[1.])); mp=np.concatenate(([1.],prec,[0.]))
    for i in range(len(mp)-2,-1,-1): mp[i]=max(mp[i],mp[i+1])
    idx=np.where(mr[1:]!=mr[:-1])[0]
    return float(np.sum((mr[idx+1]-mr[idx])*mp[idx+1]))

def map5095(recs, cls_list, conf, iou_thr_conf):
    ious = [0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95]
    aps_ = []
    for iou_m in ious:
        per_c_ap = []
        for c in cls_list:
            tps=[]; fps=[]; ngt=0
            for r in recs:
                dets=sorted([d for d in r['detections'] if d['cls']==c and d.get('confidence',0)>=conf], key=lambda d:-d.get('confidence',0))
                gts=[g for g in r['gt'] if g['cls']==c]
                used=[False]*len(gts); ngt += len(gts)
                for d in dets:
                    bi=bv=-1
                    for gi, g in enumerate(gts):
                        if used[gi]: continue
                        v=bbox_iou(d['bbox'],g['bbox'])
                        if v>bv: bv,bi=v,gi
                    if bi>=0 and bv>=iou_m:
                        used[bi]=True; tps.append(True); fps.append(False)
                    else:
                        tps.append(False); fps.append(True)
            if ngt>0: per_c_ap.append(ap(tps,fps,ngt))
        if per_c_ap: aps_.append(sum(per_c_ap)/len(per_c_ap))
    return sum(aps_)/len(aps_) if aps_ else 0.0

def score(recs, gc, miou, cls_list, ov=None):
    per_c={c:{'tp':[],'fp':[],'ngt':0} for c in cls_list}
    tp_tot=fp_tot=fn_tot=0
    per_c_thr={c:gc for c in cls_list}
    if ov: per_c_thr.update(ov)
    for r in recs:
        dets_by_cls={c:[] for c in cls_list}
        for d in r['detections']:
            if d.get('confidence',0)>=per_c_thr.get(d['cls'], gc):
                dets_by_cls.setdefault(d['cls'],[]).append(d)
        gts_by_cls={c:[] for c in cls_list}
        for g in r['gt']: gts_by_cls.setdefault(g['cls'],[]).append(g)
        for c in cls_list:
            cdets=sorted(dets_by_cls.get(c,[]), key=lambda d:-d.get('confidence',0))
            cgts=gts_by_cls.get(c,[]); used=[False]*len(cgts); per_c[c]['ngt']+=len(cgts)
            for d in cdets:
                bi=bv=-1
                for gi,g in enumerate(cgts):
                    if used[gi]: continue
                    v=bbox_iou(d['bbox'],g['bbox'])
                    if v>bv: bv,bi=v,gi
                if bi>=0 and bv>=miou:
                    used[bi]=True; per_c[c]['tp'].append(True); per_c[c]['fp'].append(False); tp_tot+=1
                else:
                    per_c[c]['tp'].append(False); per_c[c]['fp'].append(True); fp_tot+=1
            fn_tot += sum(1 for u in used if not u)
    prec=tp_tot/(tp_tot+fp_tot) if tp_tot+fp_tot>0 else 0
    rec=tp_tot/(tp_tot+fn_tot) if tp_tot+fn_tot>0 else 0
    f1=2*prec*rec/(prec+rec) if prec+rec>0 else 0
    aps=[]; apd={}
    for c in cls_list:
        if per_c[c]['ngt']>0:
            v=ap(per_c[c]['tp'], per_c[c]['fp'], per_c[c]['ngt'])
            aps.append(v); apd[c]=v
    m50=sum(aps)/len(aps) if aps else 0
    return m50, prec, rec, f1, apd, tp_tot, fp_tot, fn_tot

CLS=['open','short','mousebite','spur','copper','pin-hole']
val=json.load(open('metrics/raw/defect_val_raw.json'))
test=json.load(open('metrics/raw/defect_test_raw.json'))
print('=== ALL CANDIDATE OPS — VAL CALIBRATED, TEST LOCKED ===')
print(f'VAL  images: {len(val)}')
print(f'TEST images: {len(test)}')
print()
cands=[
    ('conf 0.25 / IoU 0.50 (ultralytics default)', 0.25, 0.50, None),
    ('conf 0.70 / IoU 0.40 (ORIGINAL CALIBRATED)', 0.70, 0.40, None),
    ('conf 0.71 / IoU 0.38 (fine-sweep val best)', 0.71, 0.38, None),
    ('conf 0.70 / IoU 0.40 / pin-hole+0.12 override', 0.70, 0.40, {'pin-hole':0.82}),
    ('conf 0.68 / IoU 0.42 / pin-hole+0.10 short+0.05', 0.68, 0.42, {'pin-hole':0.78,'short':0.73}),
]
best=None
best_test_tuple=None
for name, gc, mi, ov in cands:
    mv, pv, rv, fv, *_ = score(val, gc, mi, CLS, ov)
    score_tup=(round(fv,8), round(mv,8), round(pv,8), round(rv,8))
    if best is None or score_tup>best[0]: best=(score_tup, name, gc, mi, ov)
    mt, pt, rt, ft, apd, tp, fp, fn = score(test, gc, mi, CLS, ov)
    m95 = map5095(test, CLS, gc, mi)
    print('OP:', name)
    print(f'  VAL  -> F1={fv*100:.3f}% mAP50={mv*100:.3f}% P={pv*100:.2f}% R={rv*100:.2f}%')
    print(f'  TEST -> F1={ft*100:.3f}% mAP50={mt*100:.3f}% P={pt*100:.2f}% R={rt*100:.2f}% mAP50-95={m95*100:.2f}%  TP={tp} FP={fp} FN={fn}')
    for c in CLS:
        a = apd.get(c, 0)
        print(f'     {c:10s}: AP50={a*100:6.2f}%  ', end='')
    print()
    print()
s, bname, bgc, bmi, bov = best
mt, pt, rt, ft, apd_best, tp_best, fp_best, fn_best = score(test, bgc, bmi, CLS, bov)
m95_best = map5095(test, CLS, bgc, bmi)
gap = max(0, 0.96 - mt) * 100
print('='*70)
print('FINAL BASELINE LOCKED (from-raw deterministic, no TTA/ensemble yet)')
print('='*70)
print(f'  Selected by VAL lex-score (micro_F1, mAP50, P, R):')
print(f'    {bname}')
print(f'    conf={bgc:.4f}  match_iou={bmi:.2f}  per_class_override={bov}')
print(f'  TEST RESULTS (never used for calibration):')
print(f'    mAP50      = {mt*100:.4f}%  target ≥96%: ' + ('PASS' if mt>=0.96 else f'FAIL (gap = {gap:.2f}pp)'))
print(f'    mAP50-95   = {m95_best*100:.4f}%')
print(f'    Precision  = {pt*100:.4f}%  target ≥95%: ' + ('PASS' if pt>=0.95 else 'FAIL'))
print(f'    Recall     = {rt*100:.4f}%  target ≥95%: ' + ('PASS' if rt>=0.95 else 'FAIL'))
print(f'    F1         = {ft*100:.4f}%  target ≥95%: ' + ('PASS' if ft>=0.95 else 'FAIL'))
print(f'    TP/FP/FN   = {tp_best} / {fp_best} / {fn_best}')
print(f'    Per-class AP50:')
for c in CLS:
    a = apd_best.get(c, 0)
    bar = '█'*int(a*50)
    print(f'      {c:10s}: {a*100:6.2f}%  |{bar:<50s}|')
print()
print(f'  > mAP50 vs 96% target: GAP = {gap:.2f} percentage points')
print(f'  > TTA+ensemble fresh inference in progress (≈ 2.7h on CPU)')
print(f'  > Expected +2.0pp ±0.5pp from TTA+ensemble (documented accuracy_mode gain)')
print(f'  > Projected upper-bound (best case TTA+ensemble adds +2.5pp): {mt*100+2.5:.2f}%  → ' + ('POTENTIALLY REACHES 96%' if (mt+0.025)>=0.96 else f'STILL FAILS (expected max {mt*100+2.5:.2f}% < 96%)'))
print()
# Write result
out = {
    'baseline_locked': {
        'op_name': bname, 'global_conf': bgc, 'match_iou': bmi, 'overrides': bov,
        'VAL': {'F1': s[0], 'mAP50': s[1], 'P': s[2], 'R': s[3]},
        'TEST': {
            'mAP50': round(mt, 6), 'mAP50_95': round(m95_best, 6),
            'P': round(pt, 6), 'R': round(rt, 6), 'F1': round(ft, 6),
            'TP': int(tp_best), 'FP': int(fp_best), 'FN': int(fn_best),
            'per_class_AP50': {c: round(apd_best.get(c,0), 6) for c in CLS},
        },
        'gap_pp_vs_96_target': round(gap, 4),
        'tta_ensemble_status': 'running_background_cpu (~15s/img × 650 imgs)',
    }
}
with open('metrics/locked_baseline_96target_report.json', 'w') as f:
    json.dump(out, f, indent=2)
print('wrote: metrics/locked_baseline_96target_report.json')
