"""Verification computed from synthetic fields, never measured operational skill."""
from functools import lru_cache
import numpy as np
from scipy.ndimage import uniform_filter, gaussian_filter
from sklearn.metrics import roc_auc_score, confusion_matrix, precision_recall_fscore_support
from engine import fields, region_mask, MASK, REGIMES, probability, mixture, seed

NAMES = ['Raw NWP', 'Climatological bias removal', 'Quantile mapping', 'Global LightGBM', 'Hard regime split LightGBM', 'Soft-gated LightGBM experts', 'U-Net without regimes', 'MeghDrishti-Net', 'MeghDrishti ensemble']
METRIC_TIPS = {'bias': 'Mean forecast minus observation, in mm/day; ideal 0.', 'mae': 'Mean absolute error in mm/day; lower is better.', 'rmse': 'Root mean squared error in mm/day; lower is better.', 'pod': 'Probability of detection: hits / observed events.', 'far': 'False alarm ratio: false alarms / forecast events; lower is better.', 'csi': 'Critical success index: hits / (hits + misses + false alarms).', 'ets': 'Equitable threat score: CSI adjusted for random hits.', 'hss': 'Heidke skill score relative to random categorical agreement.', 'fss': 'Fractions skill score at a 50 km neighbourhood; higher is better.', 'bss': 'Brier skill score relative to observed event climatology.'}

def div(a, b):
    return float(a/b) if b else 0.

def fss(fc, ob, mask, threshold, size=2):
    count = uniform_filter(mask.astype(float), size=size)
    fp = uniform_filter(((fc >= threshold) & mask).astype(float), size=size) / np.maximum(count, 1e-9)
    op = uniform_filter(((ob >= threshold) & mask).astype(float), size=size) / np.maximum(count, 1e-9)
    den = np.mean(fp[mask]**2 + op[mask]**2)
    return 1 - div(np.mean((fp[mask]-op[mask])**2), den) if den else 0.

def metrics(fc, ob, mask, threshold, prob=None):
    a, b = fc[mask], ob[mask]
    pred, true = a >= threshold, b >= threshold
    h = int(np.sum(pred & true)); m = int(np.sum(~pred & true)); fa = int(np.sum(pred & ~true)); cn = int(np.sum(~pred & ~true)); n = len(a)
    chance = div((h+fa)*(h+m), n)
    prob = np.clip(a/(threshold*2), 0, 1) if prob is None else prob[mask]
    bs = np.mean((prob-true)**2)
    climate = np.mean((true-np.mean(true))**2)
    out = {'bias': float(np.mean(a-b)), 'mae': float(np.mean(np.abs(a-b))), 'rmse': float(np.sqrt(np.mean((a-b)**2))), 'pod': div(h,h+m), 'far': div(fa,h+fa), 'csi': div(h,h+m+fa), 'ets': div(h-chance,h+m+fa-chance), 'hss': div(2*(h*cn-m*fa), (h+m)*(m+cn)+(h+fa)*(fa+cn)), 'fss': fss(fc,ob,mask,threshold), 'bss': 1-div(bs,climate) if climate else 0.}
    return {k: round(v, 4) for k,v in out.items()}

def reliability(prob, observed, threshold):
    out = []
    true = observed >= threshold
    for i in range(10):
        binmask = (prob >= i/10) & (prob < (i+1)/10 if i<9 else prob<=1)
        count = int(np.sum(binmask))
        out.append({'bin': i*10+5, 'forecast': round(float(np.mean(prob[binmask]))*100, 2) if count else i*10+5, 'observed': round(float(np.mean(true[binmask]))*100, 2) if count else None, 'count': count, 'ideal': i*10+5})
    return out

def probability_report(day, lead, region, threshold, calibrated, cutoff):
    f = fields(day, lead); mask = region_mask(region)
    p = probability(f['corrected'], threshold, lead, calibrated)
    y = (f['observed'][mask]>=threshold).astype(int); pr = p[mask]
    pred = pr >= cutoff
    h = np.sum(pred & (y==1)); fa = np.sum(pred & (y==0)); m = np.sum(~pred & (y==1))
    climate = np.mean((y-np.mean(y))**2)
    return {'threshold': threshold, 'calibrated': calibrated, 'reliability': reliability(pr, f['observed'][mask], threshold), 'bss': round(1-div(np.mean((pr-y)**2),climate),3) if climate else 0, 'auc': round(float(roc_auc_score(y,pr)),3) if len(np.unique(y))>1 else None, 'pod': round(div(h,h+m),3), 'far': round(div(fa,h+fa),3), 'event_count': int(y.sum()), 'sample_count': int(len(y)), 'map': [round(float(v),3) if ok else None for v,ok in zip(p.ravel(),mask.ravel())], 'calibration_note': 'Isotonic regression fitted to five independent synthetic JJAS 2016 dates.'}

@lru_cache(maxsize=48)
def verification(day, lead, region, threshold, regime, period):
    year = int(period)
    anchor = day[5:]
    dates = [f'{year}-{anchor}'] + [f'{year}-{m:02d}-{d:02d}' for m,d in [(6,10),(6,25),(7,10),(7,25),(8,10),(8,25),(9,10)]]
    per_model = [[] for _ in NAMES]; fscores = [[] for _ in NAMES]; threshold_scores = {t: [] for t in [2.5,64.5,115.6,204.5]}
    maskbase = region_mask(region)
    all_fc = [[] for _ in NAMES]; all_ob=[]; all_reg=[]; all_fss=[[] for _ in NAMES]
    for dt in dates:
        f = fields(dt,lead); mask = maskbase.copy()
        if regime != 'All regimes':
            mask &= f['weights'].argmax(axis=0) == REGIMES.index(regime)
        if mask.sum()<2:
            continue
        forecasts = [f['raw'], np.maximum(f['raw']-np.mean(f['raw'][mask]-f['observed'][mask]),0)]
        forecasts += [f['raw']*(1-alpha) + f['corrected']*alpha for alpha in [.22,.40,.50,.66,.60,.87,1.]]
        for i,fc in enumerate(forecasts):
            p = probability(fc,threshold,lead,calibrated=i>=5)
            per_model[i].append(metrics(fc,f['observed'],mask,threshold,p))
            all_fc[i].append(fc[mask]); all_fss[i].append([fss(fc,f['observed'],mask,threshold,s) for s in [1,2,4]])
        all_ob.append(f['observed'][mask]); all_reg.append(f['weights'].argmax(axis=0)[mask])
        for t in threshold_scores:
            threshold_scores[t].append({'raw': metrics(f['raw'],f['observed'],mask,t), 'corrected':metrics(f['corrected'],f['observed'],mask,t)})
    if not all_ob:
        return {'empty': True, 'message': 'No grid samples for this region and regime combination.'}
    rng = np.random.default_rng(seed((day,lead,region,regime,period)))
    n = len(all_ob); boot = rng.integers(0,n,(120,n)); rows=[]
    raw_rmse = np.array([m['rmse'] for m in per_model[0]])
    for i,name in enumerate(NAMES):
        vals = {key: np.array([m[key] for m in per_model[i]]) for key in METRIC_TIPS}
        avg = {key: round(float(v.mean()),3) for key,v in vals.items()}
        ci = {key: [round(float(x),3) for x in np.percentile(v[boot].mean(axis=1),[2.5,97.5])] for key,v in vals.items()}
        gains = (raw_rmse-vals['rmse'])/np.maximum(raw_rmse,1e-9)*100
        rows.append({'id': f'M-{i}', 'name': name, **avg, 'ci':ci, 'improvement':round(float(gains.mean()),1), 'improvement_ci':[round(float(v),1) for v in np.percentile(gains[boot].mean(axis=1),[2.5,97.5])]})
    observed = np.concatenate(all_ob)
    frequency = []
    for lo,hi,label in [(0,2.5,'< 2.5'),(2.5,15.6,'2.5–15.6'),(15.6,64.5,'15.6–64.5'),(64.5,115.6,'64.5–115.6'),(115.6,204.5,'115.6–204.5'),(204.5,1000,'≥ 204.5')]:
        frequency.append({'category':label,'Observed':round(float(np.mean((observed>=lo)&(observed<hi)))*100,1), 'Raw NWP':round(float(np.mean((np.concatenate(all_fc[0])>=lo)&(np.concatenate(all_fc[0])<hi)))*100,1), 'Corrected':round(float(np.mean((np.concatenate(all_fc[8])>=lo)&(np.concatenate(all_fc[8])<hi)))*100,1)})
    heatmap=[]
    f = fields(dates[0],lead)
    for r,name in enumerate(REGIMES):
        for l in range(1,6):
            fl=fields(dates[0],l); mask=maskbase & (fl['weights'].argmax(axis=0)==r)
            if mask.sum()<2: gain=None
            else:
                rawerr=np.sqrt(np.mean((fl['raw'][mask]-fl['observed'][mask])**2)); correrr=np.sqrt(np.mean((fl['corrected'][mask]-fl['observed'][mask])**2));gain=round(div(rawerr-correrr,rawerr)*100,1)
            heatmap.append({'regime':name,'lead':l,'gain':gain})
    return {'empty':False, 'models':rows,'metric_tips':METRIC_TIPS,'fss':[{'scale':s,'Raw NWP':round(float(np.mean(np.array(all_fss[0])[:,j])),3),'Corrected':round(float(np.mean(np.array(all_fss[8])[:,j])),3),'Useful skill':round(.5+float(np.mean(observed>=threshold))/2,3)} for j,s in enumerate([25,50,100])], 'thresholds':[{'threshold':str(t),'Raw ETS':round(float(np.mean([v['raw']['ets'] for v in vs])),3),'Corrected ETS':round(float(np.mean([v['corrected']['ets'] for v in vs])),3),'Raw CSI':round(float(np.mean([v['raw']['csi'] for v in vs])),3),'Corrected CSI':round(float(np.mean([v['corrected']['csi'] for v in vs])),3)} for t,vs in threshold_scores.items()], 'frequency':frequency,'heatmap':heatmap,'dates':dates,'samples':int(len(observed)),'note':'Illustrative perturbation experiments, not trained models. Day-block bootstrap 95% CI (120 resamples); eight synthetic dates, not a full historical hindcast. Undefined no-event categorical scores use 0.'}

def classifier_quality(day, region):
    rng=np.random.default_rng(seed(day+region)); true=rng.choice(6,size=1200,p=[.30,.13,.17,.20,.13,.07]); probabilities=np.full((1200,6),.035)
    for i,t in enumerate(true):
        probabilities[i,t] += rng.uniform(.25,.85)
        probabilities[i,rng.integers(0,6)] += rng.uniform(.05,.55)
    probabilities/=probabilities.sum(axis=1,keepdims=True); pred=probabilities.argmax(axis=1)
    p,r,f,_=precision_recall_fscore_support(true,pred,labels=list(range(6)),zero_division=0)
    conf=probabilities.max(axis=1); ok=(true==pred)
    calibration=[]
    for lo in np.arange(0,1,.1):
        m=(conf>=lo)&(conf<lo+.1)
        if m.any():calibration.append({'forecast':round(float(conf[m].mean())*100,1),'observed':round(float(ok[m].mean())*100,1)})
    return {'matrix':confusion_matrix(true,pred,labels=list(range(6))).tolist(),'scores':[{'regime':n,'precision':round(float(p[i]),3),'recall':round(float(r[i]),3),'f1':round(float(f[i]),3)} for i,n in enumerate(REGIMES)],'calibration':calibration,'note':'Synthetic classifier samples; not outputs from a trained regime classifier.'}