"""Installation locale dans .venv et téléchargement vérifié de Fuseki."""
import hashlib,os,subprocess,sys,urllib.request,zipfile,venv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FUSEKI_VERSION='5.5.0'

def main():
    if sys.version_info<(3,11):raise SystemExit('Python 3.11 ou 3.12 est requis.')
    env=ROOT/'.venv';exe=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not exe.exists():venv.EnvBuilder(with_pip=True).create(env)
    lock=ROOT/'requirements-lock-windows-py311.txt'
    requirements=lock if os.name=='nt' and sys.version_info[:2]==(3,11) and lock.exists() else ROOT/'requirements.txt'
    stamp=env/'pharmaonto-requirements.sha256'
    wanted=hashlib.sha256(requirements.read_bytes()).hexdigest()
    if not stamp.exists() or stamp.read_text()!=wanted:
        subprocess.run([str(exe),'-m','pip','install','--cache-dir',str(ROOT/'runtime/pip-cache'),'-r',str(requirements)],check=True)
        stamp.write_text(wanted)
    dest=ROOT/'runtime'/f'apache-jena-fuseki-{FUSEKI_VERSION}'
    if not (dest/'fuseki-server.jar').exists():
        archive=ROOT/'vendor'/f'apache-jena-fuseki-{FUSEKI_VERSION}.zip'
        if not archive.exists():
            archive.parent.mkdir(parents=True,exist_ok=True)
            base=f'https://archive.apache.org/dist/jena/binaries/{archive.name}'
            print('Téléchargement officiel de Fuseki…')
            with urllib.request.urlopen(base,timeout=180) as r:archive.write_bytes(r.read())
            with urllib.request.urlopen(base+'.sha512',timeout=30) as r:sha=r.read().decode()
            (archive.with_suffix('.zip.sha512')).write_text(sha)
        digest=hashlib.sha512(archive.read_bytes()).hexdigest()
        if digest not in archive.with_suffix('.zip.sha512').read_text().lower():raise SystemExit('Empreinte Fuseki incorrecte.')
        root=(ROOT/'runtime').resolve();root.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            if any(not (root/n).resolve().is_relative_to(root) for n in z.namelist()):raise SystemExit('Archive invalide.')
            z.extractall(root)
    print('Installation terminée. Lancez DEMARRER.cmd ou .venv/Scripts/python.exe -m scripts.serve')

if __name__=='__main__':main()
