import {createContext,useContext,useEffect,useState} from 'react';
const Context=createContext(null);
export const SettingsProvider=({children})=>{
  const [date,setDate]=useState('2026-08-16');const [lead,setLead]=useState(1);const [region,setRegion]=useState('All India');const [mode,setMode]=useState('demo');
  const [theme,setTheme]=useState(localStorage.getItem('monsoon-theme')||'dark');
  const [alertCutoff,setAlertCutoff]=useState(.6);
  const [alertThresholds,setAlertThresholds]=useState({yellow:64.5,orange:115.6,red:204.5});
  useEffect(()=>{document.documentElement.classList.toggle('dark',theme==='dark');localStorage.setItem('monsoon-theme',theme);},[theme]);
  return <Context.Provider value={{date,setDate,lead,setLead,region,setRegion,mode,setMode,theme,setTheme,alertCutoff,setAlertCutoff,alertThresholds,setAlertThresholds}}>{children}</Context.Provider>;
};
export const useSettings=()=>useContext(Context);