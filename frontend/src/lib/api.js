import { useEffect, useState } from 'react';
import { useSettings } from './settings';
export const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;
export const REGIME_COLORS = {'Active':'#5595f5','Break':'#eab350','Depression':'#ad82ec','Orographic':'#45bb88','Coastal':'#35c7d5','Western Disturbance':'#ec829e','Mixed':'#8995a8'};
export const ALERT_COLORS = {Red:'#f06a76',Orange:'#ef994a',Yellow:'#e9c75c',Green:'#42ab8b'};
export const RAIN_COLORS = ['#243b58','#3c6fa0','#399cc3','#656ed4','#a661d2','#dc5ea6'];
export const pct = (v) => v == null ? '—' : `${(v*100).toFixed(0)}%`;
export function useApi(path, extra={}) {
  const {date,lead,region,mode,alertCutoff,alertThresholds}=useSettings();
  const query = new URLSearchParams({date,lead,region,mode,cutoff:alertCutoff,...alertThresholds,...extra}).toString();
  const url = `${API}${path}?${query}`;
  const [state,setState]=useState({data:null,loading:true,error:null});
  const [retry,setRetry]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();setState({data:null,loading:true,error:null});
    fetch(url,{signal:controller.signal}).then(async r=>{const body=await r.json();if(!r.ok)throw new Error(typeof body.detail==='string'?body.detail:'Unable to retrieve this product.');return body;}).then(data=>setState({data,loading:false,error:null})).catch(e=>{if(e.name!=='AbortError')setState({data:null,loading:false,error:e.message});});
    return()=>controller.abort();
  },[url,retry]);
  return {...state,retry:()=>setRetry(v=>v+1)};
}
export function download(content,name,type='text/plain') {const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export async function copy(text) {await navigator.clipboard.writeText(text);}