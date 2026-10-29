"""Démarre les deux services, vérifie les ports et arrête ses propres processus."""
import argparse,os,socket,subprocess,sys,time,urllib.request,json,webbrowser
from pathlib import Path
from .build_ontology import ROOT

def busy(port):
    with socket.socket() as s:return s.connect_ex(('127.0.0.1',port))==0

def main():
    p=argparse.ArgumentParser();p.add_argument('--local',action='store_true',help='RDFLib explicite, sans Fuseki');p.add_argument('--no-browser',action='store_true');args=p.parse_args()
    if busy(8000):raise SystemExit('Le port 8000 est déjà utilisé. Arrêtez l’autre application avant de démarrer.')
    children=[];env=os.environ.copy();env['PHARMA_BACKEND']='rdflib' if args.local else 'fuseki'
    try:
        if not args.local:
            if busy(3030):raise SystemExit('Le port 3030 est déjà utilisé. Arrêtez l’autre Fuseki avant de démarrer.')
            jar=ROOT/'runtime/apache-jena-fuseki-5.5.0/fuseki-server.jar'
            if not jar.exists():raise SystemExit('Fuseki absent. Lancez INSTALLER.cmd.')
            java=str(Path(env['JAVA_HOME'])/'bin/java') if env.get('JAVA_HOME') else 'java'
            env['FUSEKI_BASE']=str(ROOT/'runtime/fuseki-base')
            env['FUSEKI_HOME']=str(jar.parent)
            child=subprocess.Popen([java,'-Xmx1G','-jar',str(jar),'--localhost','--port=3030','--file='+str(ROOT/'ontology/pharmaonto-materialized.ttl'),'/pharmaonto'],cwd=ROOT,env=env)
            children.append(child)
            for _ in range(90):
                if child.poll() is not None:raise RuntimeError('Fuseki n’a pas démarré. Vérifiez Java 17 ou plus.')
                if busy(3030):break
                time.sleep(1)
            else:raise RuntimeError('Délai de démarrage Fuseki dépassé.')
        child=subprocess.Popen([sys.executable,str(ROOT/'manage.py'),'runserver','127.0.0.1:8000','--noreload'],cwd=ROOT,env=env);children.append(child)
        for _ in range(90):
            if child.poll() is not None:raise RuntimeError('Django n’a pas démarré.')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2) as r:
                    if json.load(r).get('ready'):break
            except (OSError,ValueError):pass
            time.sleep(1)
        else:raise RuntimeError('L’application ne répond pas avec le graphe attendu.')
        print('\nPharmaOnto prêt : http://127.0.0.1:8000\nCtrl+C arrête les deux services.\n',flush=True)
        if not args.no_browser:webbrowser.open('http://127.0.0.1:8000')
        while all(c.poll() is None for c in children):time.sleep(1)
        raise RuntimeError('Un service s’est arrêté. Consultez les messages ci-dessus.')
    except KeyboardInterrupt:print('\nArrêt de PharmaOnto.')
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:child.kill();child.wait()

if __name__=='__main__':main()
