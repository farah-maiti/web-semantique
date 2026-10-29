import json,os,re
from functools import lru_cache
from pathlib import Path
import requests
from rdflib import Graph,RDF,RDFS,OWL,URIRef
from scripts.build_ontology import ROOT,P
from .queries import query


class BackendUnavailable(Exception):pass

@lru_cache(maxsize=1)
def local_graph():
    return Graph().parse(ROOT/'ontology/pharmaonto-materialized.ttl',format='turtle')

def backend():
    return os.environ.get('PHARMA_BACKEND','fuseki').lower()

def execute(sparql):
    if backend()=='rdflib':return json.loads(local_graph().query(sparql).serialize(format='json'))
    if backend()!='fuseki':raise BackendUnavailable('PHARMA_BACKEND doit valoir fuseki ou rdflib.')
    endpoint=os.environ.get('FUSEKI_URL','http://127.0.0.1:3030/pharmaonto/query')
    try:
        r=requests.post(endpoint,data={'query':sparql},headers={'Accept':'application/sparql-results+json'},timeout=(3,15))
        r.raise_for_status();return r.json()
    except (requests.RequestException,ValueError) as error:
        raise BackendUnavailable('Fuseki indisponible. Démarrez Fuseki, ou sélectionnez explicitement le mode RDFLib local.') from error

def rows(result):
    return [{k:v['value'] for k,v in row.items()} for row in result.get('results',{}).get('bindings',[])]

def health():
    result=execute('SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }')
    count=int(rows(result)[0]['triples'])
    expected=json.loads((ROOT/'validation/counts.json').read_text())['materialized_triples']
    checks=execute('PREFIX po: <http://www.esprit.tn/pharmaonto#> ASK { po:Advil_400 a po:MedicamentAntiInflammatoire ; po:estContreIndiquePour po:Patient_P002 . po:DiabeteType2 po:estTraitePar po:Glucophage_850 . }')
    return {'backend':backend(),'triples':count,'expected_triples':expected,'ready':count==expected and checks.get('boolean',False)}

def entity_graph(patient):
    # Public IDs come from the fixed fictional corpus, never arbitrary IRIs.
    data=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf-8'))
    if patient not in {p['id'] for p in data['patients']}:raise ValueError('Patient inconnu')
    sparql='''PREFIX po: <http://www.esprit.tn/pharmaonto#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?s ?p ?o ?labelS ?labelO WHERE {
 VALUES ?patient { po:__PATIENT__ }
 { ?patient ?p ?o . BIND(?patient AS ?s) VALUES ?p {po:prend po:souffreDe} }
 UNION { ?patient po:prend ?s . ?s ?p ?o . VALUES ?p {po:contientPrincipeActif po:aPourContreIndication po:estContreIndiquePour po:interactionMedicamenteuseAvec}
 FILTER(?p != po:estContreIndiquePour || ?o = ?patient)
 FILTER(?p != po:interactionMedicamenteuseAvec || EXISTS { ?patient po:prend ?o }) }
 UNION { ?patient po:prend/po:aPourContreIndication ?s . ?s po:concerne ?o . BIND(po:concerne AS ?p) }
 ?s rdfs:label ?labelS . ?o rdfs:label ?labelO .
} LIMIT 100'''.replace('__PATIENT__',patient)
    return rows(execute(sparql))
