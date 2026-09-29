"""Create a verified source archive, excluding private configuration and artifacts."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'frontend/public/downloads/MonsoonLens-source.zip'
EXCLUDED = {'node_modules','build','dist','.git','.venv','venv','__pycache__',
            '.pytest_cache','.ruff_cache','.cache','coverage','downloads','test_reports'}

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    files=[]
    for folder in ['frontend','backend','scripts','tests','memory']:
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or p.is_symlink():
                continue
            rel=p.relative_to(ROOT)
            if any(part in EXCLUDED for part in rel.parts):
                continue
            if p.name.startswith('.env') and p.name!='.env.example':
                continue
            if p.suffix in {'.pyc','.pyo','.log','.pem','.key','.zip'}:
                continue
            files.append(p)
    files.extend(ROOT/n for n in ['README.md','EXPORT_GUIDE.md','.gitignore'] if (ROOT/n).is_file())
    with ZipFile(OUTPUT,'w',ZIP_DEFLATED,compresslevel=8) as archive:
        for p in sorted(set(files)):
            archive.write(p,'MonsoonLens/'+str(p.relative_to(ROOT)))
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        names=archive.namelist()
        assert not any(Path(n).name=='.env' for n in names)
        for required in ['backend/server.py','backend/data/india.geojson',
                         'frontend/public/data/india.geojson','frontend/public/data/land-context.geojson',
                         'backend/data/districts-display.geojson','scripts/prepare_official_india.py']:
            assert 'MonsoonLens/'+required in names
        print(f'Verified source archive: {len(names)} files, {OUTPUT.stat().st_size/1024/1024:.2f} MiB')

if __name__=='__main__':
    main()