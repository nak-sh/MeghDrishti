import './App.css';
import {BrowserRouter,Routes,Route} from 'react-router-dom';
import {SettingsProvider} from './lib/settings';
import {Layout} from './components/Layout';
import {Toaster} from './components/ui/sonner';
import CommandCenter from './pages/CommandCenter';
import Districts from './pages/Districts';
import Forecast from './pages/Forecast';
import Probabilities from './pages/Probabilities';
import Regimes from './pages/Regimes';
import Verification from './pages/Verification';
import CaseStudy from './pages/CaseStudy';
import Alerts from './pages/Alerts';
import Architecture from './pages/Architecture';
import Methodology from './pages/Methodology';
export default function App(){return <SettingsProvider><BrowserRouter><Layout><Routes><Route path="/" element={<CommandCenter/>}/><Route path="/districts" element={<Districts/>}/><Route path="/forecast" element={<Forecast/>}/><Route path="/probabilities" element={<Probabilities/>}/><Route path="/regimes" element={<Regimes/>}/><Route path="/verification" element={<Verification/>}/><Route path="/case-study" element={<CaseStudy/>}/><Route path="/alerts" element={<Alerts/>}/><Route path="/architecture" element={<Architecture/>}/><Route path="/methodology" element={<Methodology/>}/><Route path="*" element={<CommandCenter/>}/></Routes></Layout><Toaster richColors position="bottom-right"/></BrowserRouter></SettingsProvider>}