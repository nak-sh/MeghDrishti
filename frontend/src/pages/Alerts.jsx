import {useState,useEffect} from 'react';
import {Copy,Download,Play,Code2,Radio} from 'lucide-react';
import {API,useApi,download,copy} from '../lib/api';
import {useSettings} from '../lib/settings';
import {Async,PageTitle,SectionHead,Btn,Select,Notice} from '../components/Primitives';
import {toast} from 'sonner';

const endpoints=[
 ['/forecast/districts','District rainfall, exceedance and alerts'],
 ['/forecast/grid','0.25° rainfall fields and grid metadata'],
 ['/regime','Soft regime mixtures and diagnostics'],
 ['/probabilities','Exceedance probability and reliability'],
 ['/verification','Computed synthetic verification metrics'],
 ['/alerts/cap/{district}','CAP 1.2 XML · status Test']
];
const highlightXML=xml=>xml.split(/(<[^>]+>)/g).map((part,i)=><span key={i} className={part.startsWith('<')?'xml-tag':'xml-text'}>{part}</span>);
const copyText=async text=>{try{await copy(text);toast.success('Copied to clipboard');}catch(e){toast.error('Clipboard unavailable in this browser');}};

const Endpoint=({path,label,selected,query})=>{
 const [response,setResponse]=useState(null);const [loading,setLoading]=useState(false);
 const id=path.replace(/^\//,'').replace(/[^a-z]+/g,'-').replace(/-$/,'');
 const url=`${API}${path.replace('{district}',selected||'DISTRICT_ID')}?${query}`;
 const curl=`curl -X GET '${url}'`;
 useEffect(()=>{setResponse(null);},[url]);
 const tryAPI=async()=>{
   setLoading(true);
   try{const r=await fetch(url);const contentType=r.headers.get('content-type')||'';const body=contentType.includes('json')?JSON.stringify(await r.json(),null,2):await r.text();setResponse({status:r.status,body});}
   catch(e){setResponse({status:'Error',body:e.message});}
   finally{setLoading(false);}
 };
 return <div className="api-endpoint" data-testid={`api-endpoint-${id}`}>
   <div className="endpoint-row"><span className="http-method">GET</span><div><code data-testid={`api-path-${id}`}>/api{path}</code><p>{label}</p></div><Btn id={`api-try-${id}`} icon={Play} onClick={tryAPI} disabled={loading||(path.includes('{district}')&&!selected)}>{loading?'Loading…':'Try it'}</Btn></div>
   <div className="curl-row"><code data-testid={`api-curl-${id}`}>{curl}</code><button data-testid={`api-copy-${id}`} className="icon-button" title="Copy curl command" onClick={()=>copyText(curl)}><Copy size={14}/></button></div>
   {response&&<div className="api-response"><span data-testid={`api-status-${id}`}>HTTP {response.status}</span><pre data-testid={`api-response-${id}`}>{response.body.length>30000?response.body.slice(0,30000)+'\n… preview truncated; copy the full response below':response.body}</pre><Btn id={`api-response-copy-${id}`} icon={Copy} onClick={()=>copyText(response.body)}>Copy full response</Btn></div>}
 </div>;
};

export default function Alerts(){
 const s=useSettings();const districts=useApi('/forecast/districts');const [selected,setSelected]=useState('');const [xml,setXML]=useState('');const [capError,setCapError]=useState('');const [busy,setBusy]=useState(false);
 useEffect(()=>{if(districts.data?.districts.length&&!districts.data.districts.some(d=>d.id===selected))setSelected(districts.data.districts[0].id);},[districts.data,selected]);
 const query=new URLSearchParams({date:s.date,lead:s.lead,region:s.region,mode:s.mode,cutoff:s.alertCutoff,...s.alertThresholds}).toString();
 useEffect(()=>{
   if(!selected)return;
   const controller=new AbortController();setXML('');setCapError('');setBusy(true);
   fetch(`${API}/alerts/cap/${selected}?${query}`,{signal:controller.signal})
    .then(async r=>{if(!r.ok){const e=await r.json();throw Error(e.detail);}return r.text();})
    .then(setXML).catch(e=>{if(e.name!=='AbortError')setCapError(e.message);})
    .finally(()=>{if(!controller.signal.aborted)setBusy(false);});
   return()=>controller.abort();
 },[selected,query]);
 return <>
   <PageTitle title="Alerts & API" description="Inspectable products, portable formats, and a stable interface for future model outputs."><span className="technical-tag"><Radio size={14}/> TEST MESSAGES ONLY</span></PageTitle>
   <Notice>CAP messages are generated with status “Test”. No alerts are issued or transmitted to the public.</Notice>
   <section className="cap-section"><SectionHead title="CAP 1.2 alert generator" sub="Common Alerting Protocol · XML product preview"/>
     <Async state={districts}>{data=><>
       <div className="cap-controls"><Select id="cap-district-select" label="DISTRICT" value={selected} onChange={e=>setSelected(e.target.value)}>{data.districts.map(d=><option key={d.id} value={d.id}>{`${d.name} · ${d.state}`}</option>)}</Select><div><Btn id="cap-copy" icon={Copy} disabled={!xml} onClick={()=>copyText(xml)}>Copy XML</Btn><Btn id="cap-download" icon={Download} disabled={!xml} onClick={()=>download(xml,`monsoonlens-test-alert-${selected}.xml`,'application/xml')}>Download .xml</Btn></div></div>
       {busy?<div className="skeleton sk-large" data-testid="cap-loading"/>:capError?<div className="error-state" data-testid="cap-error">{capError}</div>:<div className="code-panel"><div className="code-header"><span><Code2 size={14}/> alert.xml</span><span>CAP 1.2 <i/> TEST</span></div><pre data-testid="cap-xml-preview">{highlightXML(xml)}</pre></div>}
     </>}</Async>
   </section>
   <section className="api-explorer"><SectionHead title="API explorer" sub="Same REST contract for demo and future live products"/>{endpoints.map(([path,label])=><Endpoint key={path} path={path} label={label} selected={selected} query={query}/>)}</section>
 </>;
}