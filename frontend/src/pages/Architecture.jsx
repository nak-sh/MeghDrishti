import { PageTitle } from '../components/Primitives';

export default function Architecture() {
  return (
    <>
      <PageTitle title="Architecture & Operations" description="System architecture diagram." />
      <div className="architecture-layout" style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
        <img 
          src="/logo.png" 
          alt="Architecture Diagram" 
          style={{ maxWidth: '100%', borderRadius: '8px' }}
        />
      </div>
    </>
  );
}