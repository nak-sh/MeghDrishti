import os
import json
from datetime import date as Date, timedelta
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree as ET
import numpy as np
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')
from engine import fields, districts, clean_grid, mixture, region_mask, REGIONS, REGIMES, COLORS, GEO, seed, BOUNDARY_PROVENANCE
from metrics import metrics, probability_report, verification, classifier_quality
from content import metadata, methodology, RULES, PIPELINE

app=FastAPI(title='MeghDrishti prototype API', version='0.1.0', description='Synthetic rainfall demonstration. Not an operational forecasting service.')
app.add_middleware(CORSMiddleware,allow_origins=os.environ['CORS_ORIGINS'].split(','),allow_credentials=False,allow_methods=['GET'],allow_headers=['*'])
api=APIRouter(prefix='/api')
def context(date:Date=Query(Date(2026,8,16)),lead:int=Query(1,ge=1,le=5),region:str='All India',mode:Literal['demo','live']='demo'):
    if mode=='live': raise HTTPException(503,'Live service is not connected. Provide the service URL, authentication details and response schema to enable live products. No synthetic data is substituted for live data.')
    if region not in REGIONS:raise HTTPException(422,'Unknown region preset.')
    if date.year<2000 or date.year>2100:raise HTTPException(422,'Date must be between 2000 and 2100.')
    return {'day':date.isoformat(),'lead':lead,'region':region}

def meta(c):
    return {'data_mode':'demo','synthetic':True,'initialization_date':c['day'],'lead':c['lead'],'region':c['region'],'disclaimer':'Synthetic data for prototype demonstration. Metrics are illustrative, not measured results.','boundary_source':BOUNDARY_PROVENANCE['source'],'boundary_representation':BOUNDARY_PROVENANCE['boundary_representation']}

@api.get('/')
def root():return {'service':'MeghDrishti','status':'ok','synthetic':True}
@api.get('/metadata')
def get_metadata():return metadata()
@api.get('/overview')
def overview(c=Depends(context),cutoff:float=Query(.6,ge=.05,le=.99),yellow:float=Query(64.5,ge=1,le=500),orange:float=Query(115.6,ge=1,le=500),red:float=Query(204.5,ge=1,le=500)):
    if not yellow<orange<red:raise HTTPException(422,'Rainfall thresholds must increase: Yellow < Orange < Red.')
    ds=districts(**c,cutoff=cutoff,yellow=yellow,orange=orange,red=red);f=fields(c['day'],c['lead']);mix=mixture(f['weights'],region_mask(c['region']));dominant=max(mix,key=mix.get)
    return {**meta(c),'districts':ds,'counts':{a:sum(d['alert']==a for d in ds) for a in ['Red','Orange','Yellow','Green']},'dominant':dominant,'mix':mix,'mixed':sum(v>.3 for v in mix.values())>=2,'confidence':round(float(np.mean(f['weights'].max(axis=0)[region_mask(c['region'])])),3),'highest_probability':max([d['p64'] for d in ds],default=0),'run_time':c['day']+'T00:00:00Z','latency_seconds':round(36+(seed(c['day'])%170)/10,1),'valid_date':f['valid_date'],'metrics':metrics(f['corrected'],f['observed'],region_mask(c['region']),64.5),'latency_note':'Illustrative product latency, not measured.'}
@api.get('/forecast/districts')
def get_districts(c=Depends(context),cutoff:float=Query(.6,ge=.05,le=.99),yellow:float=Query(64.5,ge=1,le=500),orange:float=Query(115.6,ge=1,le=500),red:float=Query(204.5,ge=1,le=500),format:Literal['json','geojson']='json'):
    if not yellow<orange<red:raise HTTPException(422,'Rainfall thresholds must increase: Yellow < Orange < Red.')
    ds=districts(**c,cutoff=cutoff,yellow=yellow,orange=orange,red=red)
    if format=='geojson':
        lookup={d['id']:d for d in ds}
        return {'type':'FeatureCollection',**meta(c),'features':[{'type':'Feature','geometry':f['geometry'],'properties':lookup[f['properties']['id']]} for f in GEO['features'] if f['properties']['id'] in lookup]}
    return {**meta(c),'districts':ds,'mapping':{'cutoff':cutoff,'yellow':yellow,'orange':orange,'red':red,'status':'To be confirmed with NCMRWF/IMD'}}
@api.get('/forecast/grid')
def grid(c=Depends(context)):
    f=fields(c['day'],c['lead']);mask=region_mask(c['region'])
    return {**meta(c),**clean_grid(**c),'metrics':{layer:metrics(f[layer],f['observed'],mask,64.5) for layer in ['raw','corrected','observed']}}
@api.get('/forecast/point')
def point(lat:float=Query(...,ge=-90,le=90),lon:float=Query(...,ge=-180,le=180),c=Depends(context)):
    from engine import LATS,LONS,MASK,probability,THRESHOLDS
    iy=int(np.argmin(abs(LATS-lat)));ix=int(np.argmin(abs(LONS-lon)))
    if abs(float(LATS[iy])-lat)>.25 or abs(float(LONS[ix])-lon)>.25 or not MASK[iy,ix]:raise HTTPException(404,'No land-grid data at this location.')
    f=fields(c['day'],c['lead'])
    return {**meta(c),'lat':float(LATS[iy]),'lon':float(LONS[ix]),**{n:round(float(f[n][iy,ix]),1) for n in ['raw','corrected','observed']},'mix':{r:round(float(f['weights'][i,iy,ix]),3) for i,r in enumerate(REGIMES)},'probabilities':{str(t):round(float(probability(f['corrected'],t,c['lead'])[iy,ix]),3) for t in THRESHOLDS}}
@api.get('/regime')
def regimes(c=Depends(context)):
    f=fields(c['day'],c['lead']);regions=[]
    for name in ['Western Ghats','Himalaya','Indo-Gangetic Plains','Northeast','Central India']:
        mix=mixture(f['weights'],region_mask(name));regions.append({'region':name,**mix,'mixed':sum(v>.3 for v in mix.values())>=2})
    timeline=[];year=int(c['day'][:4]);start=Date(year,6,1)
    for offset in range(0,122,3):
        dt=(start+timedelta(days=offset)).isoformat(); ff=fields(dt,c['lead']);timeline.append({'date':dt,'label':dt[5:],**mixture(ff['weights'],region_mask(c['region']))})
    return {**meta(c),'regions':regions,'timeline':timeline,'rules':RULES,'quality':classifier_quality(c['day'],c['region']),'mix':mixture(f['weights'],region_mask(c['region']))}
@api.get('/probabilities')
def probabilities(c=Depends(context),threshold:float=64.5,calibrated:bool=True,cutoff:float=Query(.5,ge=0,le=1)):
    if threshold not in [64.5,115.6,204.5]:raise HTTPException(422,'Unsupported probability threshold.')
    return {**meta(c),**probability_report(**c,threshold=threshold,calibrated=calibrated,cutoff=cutoff)}
@api.get('/verification')
def verify(c=Depends(context),threshold:float=64.5,regime:str='All regimes',period:Literal['2017','2018','2019']='2018'):
    if threshold not in [2.5,64.5,115.6,204.5]:raise HTTPException(422,'Unsupported verification threshold.')
    if regime!='All regimes' and regime not in REGIMES:raise HTTPException(422,'Unknown regime.')
    # Leap-day filter uses Feb 28 when the selected test year is not a leap year.
    day=c['day']
    try: Date.fromisoformat(period+day[4:])
    except ValueError:day=day[:4]+'-02-28'
    return {**meta(c),**verification(day,c['lead'],c['region'],threshold,regime,period)}
@api.get('/case-study')
def case_study(c=Depends(context)):
    timeline=[]
    for d in range(10,20):
        dt=f'2018-08-{d}';f=fields(dt,c['lead']);mask=region_mask('Kerala');mix=mixture(f['weights'],mask)
        timeline.append({'date':dt,'day':f'{d} Aug','raw':round(float(f['raw'][mask].mean()),1),'corrected':round(float(f['corrected'][mask].mean()),1),'observed':round(float(f['observed'][mask].mean()),1),**mix})
    first_raw=next((i for i,d in enumerate(timeline) if d['raw']>=115.6),None);first_corrected=next((i for i,d in enumerate(timeline) if d['corrected']>=115.6),None)
    gain=(first_raw-first_corrected)*24 if first_raw is not None and first_corrected is not None else None
    return {**meta(c),'timeline':timeline,'warning_hours':gain,'warning_note':'Illustrative lead gained at 115.6 mm/day Kerala areal-mean threshold; computed from this synthetic sequence. Not a historical warning assessment.','narrative':'In this synthetic reconstruction inspired by the August 2018 Kerala floods, damped and displaced raw rainfall misses the strength of the Western Ghats rain core. The corrected surrogate restores part of the orographic signal. Actual event attribution and warning benefit require real hindcast evaluation.','event':'Kerala · 10–19 August 2018'}
@api.get('/alerts/cap/{district}')
def cap(district:str,c=Depends(context),cutoff:float=Query(.6,ge=.05,le=.99),yellow:float=Query(64.5,ge=1,le=500),orange:float=Query(115.6,ge=1,le=500),red:float=Query(204.5,ge=1,le=500)):
    if not yellow<orange<red:raise HTTPException(422,'Rainfall thresholds must increase: Yellow < Orange < Red.')
    ds=districts(c['day'],c['lead'],'All India',cutoff,yellow,orange,red);d=next((d for d in ds if d['id']==district),None)
    if not d:raise HTTPException(404,'District not found.')
    ns='urn:oasis:names:tc:emergency:cap:1.2';ET.register_namespace('',ns)
    node=lambda parent,name,value:ET.SubElement(parent,'{'+ns+'}'+name)
    root=ET.Element('{'+ns+'}alert')
    def add(parent,key,value): n=node(parent,key,value);n.text=str(value);return n
    valid=Date.fromisoformat(fields(c['day'],c['lead'])['valid_date'])
    for k,v in [('identifier',f'meghdrishti-test-{district}-{c["day"]}-d{c["lead"]}'),('sender','prototype@meghdrishti.invalid'),('sent',c['day']+'T00:00:00+00:00'),('status','Test'),('msgType','Alert'),('scope','Public')]:add(root,k,v)
    info=node(root,'info','')
    for k,v in [('language','en-IN'),('category','Met'),('event','Synthetic heavy rainfall demonstration'),('responseType','Monitor'),('urgency','Future'),('severity',{'Red':'Extreme','Orange':'Severe','Yellow':'Moderate','Green':'Minor'}[d['alert']]),('certainty','Possible'),('effective',valid.isoformat()+'T03:00:00+00:00'),('expires',(valid+timedelta(days=1)).isoformat()+'T03:00:00+00:00'),('senderName','MeghDrishti prototype — not an official warning agency'),('headline',f'TEST ONLY: {d["alert"]} rainfall product for {d["name"]}'),('description','Synthetic data for prototype demonstration. Not an operational alert.'),('instruction',d['action']+' Do not act on this test message.')]:add(info,k,v)
    area=node(info,'area','');add(area,'areaDesc',f'{d["name"]}, {d["state"]}');add(area,'circle',f'{d["lat"]},{d["lon"]} 10')
    ET.indent(root,space='  ')
    return Response(ET.tostring(root,encoding='utf-8',xml_declaration=True),media_type='application/xml')
@api.get('/architecture')
def architecture(c=Depends(context)):return {**meta(c),'layers':PIPELINE}
@api.get('/operations')
def operations(c=Depends(context)):
    return {**meta(c),'status':'Demo engine ready','last_run':c['day']+'T00:00:00Z','latency_seconds':round(36+(seed(c['day'])%170)/10,1),'missing_inputs':['Live NWP feed','IMD observations','Trained model artifacts'],'model_version':'synthetic-engine-v0.1','history':[{'version':'synthetic-engine-v0.1','date':c['day'],'status':'Active demo generator','note':'Date-seeded fields and isotonic calibration'},{'version':'synthetic-engine-v0.0','date':'2026-06-01','status':'Archived design record','note':'Initial field-generation specification'}],'alerts':[{'time':'00:00 UTC','message':'Synthetic forecast cycle generated','level':'Info'},{'time':'00:00 UTC','message':'Operational input feeds not connected','level':'Warning'},{'time':'00:00 UTC','message':'Public alert dissemination disabled','level':'Info'}]}
@api.get('/methodology')
def method(c=Depends(context)):return {**meta(c),**methodology()}
app.include_router(api)