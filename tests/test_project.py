import json,os
from pathlib import Path
import pytest
from rdflib import Graph,RDF,OWL,Literal,XSD
from pyshacl import validate
from scripts.build_ontology import ROOT,P
from scripts.reason import check
from webapp.queries import QUERIES,query
from webapp.nlp import EXAMPLES,translate,UnsupportedQuestion

@pytest.fixture(scope='module')
def asserted():return Graph().parse(ROOT/'ontology/pharmaonto.owl')
@pytest.fixture(scope='module')
def materialized():return Graph().parse(ROOT/'ontology/pharmaonto-materialized.ttl',format='turtle')

def test_serializations_equivalent(asserted):
    from rdflib.compare import isomorphic
    assert isomorphic(asserted,Graph().parse(ROOT/'ontology/pharmaonto.ttl',format='turtle'))

def test_counts_derived_from_graph(asserted,materialized):
    counts=json.loads((ROOT/'validation/counts.json').read_text())
    for key,kind in [('classes',OWL.Class),('object_properties',OWL.ObjectProperty),('data_properties',OWL.DatatypeProperty),('individuals',OWL.NamedIndividual)]:
        assert counts[key]==len([s for s in asserted.subjects(RDF.type,kind) if str(s).startswith(str(P))])
    assert counts['asserted_triples']==len(asserted)
    assert counts['materialized_triples']==len(materialized)

def test_shacl_accepts_corpus(asserted):
    ok,_,text=validate(asserted,shacl_graph=str(ROOT/'ontology/shapes.ttl'),inference='rdfs')
    (ROOT/'validation/shacl.log').write_text(text,encoding='utf-8')
    assert ok

@pytest.mark.parametrize('fault',['missing_name','negative_strength','missing_reference','adult_with_child_age','missing_source'])
def test_shacl_rejects_bad_data(asserted,fault):
    g=Graph();g+=asserted
    if fault=='missing_name':g.remove((P.Advil_400,P.nomCommercial,None))
    elif fault=='negative_strength':g.set((P.Advil_400,P.dosageMg,Literal('-2',datatype=XSD.decimal)))
    elif fault=='missing_reference':g.remove((P.Amoxicilline_BGR_1g,P.estGeneriqueDe,None))
    elif fault=='adult_with_child_age':g.set((P.Patient_P001,P.age,Literal(5,datatype=XSD.integer)))
    else:
        from scripts.build_ontology import DCT
        g.remove((P.Advil_400,DCT.source,None))
    assert not validate(g,shacl_graph=str(ROOT/'ontology/shapes.ttl'),inference='rdfs')[0]

@pytest.mark.parametrize('fault',['disjoint_types','two_distinct_references'])
def test_hermit_detects_contradictions(asserted,tmp_path,fault):
    g=Graph();g+=asserted
    if fault=='disjoint_types':g.add((P.Clamoxyl_1g,RDF.type,P.Generique))
    else:g.add((P.Amoxicilline_BGR_1g,P.estGeneriqueDe,P.Glucophage_850))
    f=tmp_path/'bad.owl';g.serialize(f,format='xml');r=check(f)
    assert r.returncode==2 and 'consistent=false' in r.stdout

def test_open_world_missing_reference_not_inconsistent(asserted,tmp_path):
    g=Graph();g+=asserted;g.remove((P.Amoxicilline_BGR_1g,P.estGeneriqueDe,None))
    f=tmp_path/'incomplete.owl';g.serialize(f,format='xml');r=check(f)
    assert r.returncode==0 and 'consistent=true' in r.stdout

def test_inferences_are_not_asserted(asserted,materialized):
    expected=[(P.Advil_400,RDF.type,P.MedicamentAntiInflammatoire),(P.Warfarine,P.interagitAvec,P.Ibuprofene),(P.DiabeteType2,P.estTraitePar,P.Glucophage_850),(P.Advil_400,P.estContreIndiquePour,P.Patient_P002),(P.Glucophage_850,P.provoque,P.AcidoseLactique)]
    for triple in expected:assert triple not in asserted and triple in materialized

def test_three_contraindication_alerts(materialized):
    assert set(materialized.subject_objects(P.estContreIndiquePour))=={(P.Advil_400,P.Patient_P002),(P.Amoxicilline_BGR_1g,P.Patient_P003),(P.Metformine_BGR_850,P.Patient_P005)}

def test_patient_interaction_and_control(materialized):
    r=list(materialized.query(query('interactions_patient')))
    assert len(r)==1 and r[0].patient==P.Patient_P004
    assert not list(materialized.triples((None,P.estContreIndiquePour,P.Patient_P001)))

@pytest.mark.parametrize('key',list(QUERIES))
def test_queries_run(key,materialized):assert len(list(materialized.query(query(key))))>0

@pytest.mark.parametrize('q,expected',list(zip(EXAMPLES,[1,1,2,2,1,2,1,4,1,6])))
def test_nlp_example_answers(q,expected,materialized):assert len(list(materialized.query(translate(q)['sparql'])))==expected

@pytest.mark.parametrize('q',['','Quel traitement me conseillez-vous ?','Quels médicaments sans effets secondaires ?','Quels sont les effets secondaires de l’aspirine ?','Quelles alertes pour P999 ?','Effets de Glucophage et Advil','Effets de Glucophage pour le patient P002','Quels médicaments coûtent moins de 10 euros ?','Quels médicaments traitent le diabète sans metformine ?','Quels médicaments sont anti-inflammatoires et antibiotiques ?','Quels médicaments traitent le diabète et l’hypertension ?'])
def test_unsupported_questions(q):
    with pytest.raises(UnsupportedQuestion):translate(q)

def test_question_cannot_inject_sparql():
    q='Quels médicaments contiennent metformine } SERVICE <http://example.org> { ?s ?p ?o'
    with pytest.raises(UnsupportedQuestion):translate(q)

@pytest.fixture(scope='module')
def client():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','webapp.settings')
    import django;django.setup()
    from django.test import Client
    return Client(enforce_csrf_checks=True)

def test_api_and_csrf(client,monkeypatch):
    monkeypatch.setenv('PHARMA_BACKEND','rdflib')
    assert client.get('/').status_code==200
    token=client.cookies['csrftoken'].value
    assert client.post('/api/ask',data=json.dumps({'question':EXAMPLES[0]}),content_type='application/json').status_code==403
    response=client.post('/api/ask',data=json.dumps({'question':EXAMPLES[0]}),content_type='application/json',HTTP_X_CSRFTOKEN=token)
    assert response.status_code==200 and len(response.json()['result']['results']['bindings'])==1
    assert client.get('/api/health').json()['ready']
    assert client.get('/api/query/invalid').status_code==404
    assert client.get('/api/graph?patient=P999').status_code==400
    for number in range(1,6):
        patient=f'Patient_P00{number}'
        edges=client.get('/api/graph?patient='+patient).json()['edges']
        assert edges
        patients={value for edge in edges for value in (edge['s'],edge['o']) if '#Patient_' in value}
        assert patients=={str(P[patient])},patient
        assert all(edge['s']==str(P[patient]) for edge in edges if edge['p'] in (str(P.prend),str(P.souffreDe)))

def test_backend_failure_is_explicit(monkeypatch):
    from webapp.semantic import execute,BackendUnavailable
    monkeypatch.setenv('PHARMA_BACKEND','fuseki');monkeypatch.setenv('FUSEKI_URL','http://127.0.0.1:1/pharmaonto/query')
    with pytest.raises(BackendUnavailable):execute(query('catalogue'))

@pytest.mark.integration
def test_fuseki_matches_rdflib_for_every_query(materialized,monkeypatch):
    if os.environ.get('RUN_FUSEKI_TESTS')!='1':pytest.skip('Activer RUN_FUSEKI_TESTS=1 après démarrage de Fuseki.')
    from webapp.semantic import execute
    monkeypatch.setenv('PHARMA_BACKEND','fuseki')
    results=[]
    for key in QUERIES:
        sparql=query(key)
        a=json.loads(materialized.query(sparql).serialize(format='json'))['results']['bindings']
        b=execute(sparql)['results']['bindings']
        # GROUP_CONCAT order is unspecified. Compare its members as a set.
        def canonical(rows):
            values=[]
            for row in rows:
                obj={k:sorted(v['value'].split(', ')) if k=='medicaments' else v['value'] for k,v in row.items()}
                values.append(json.dumps(obj,sort_keys=True,ensure_ascii=False))
            return sorted(values)
        assert canonical(a)==canonical(b),key
        results.append({'query':key,'rows':len(b),'same_answers':True})
    from webapp.semantic import entity_graph
    for number in range(1,6):
        patient=f'Patient_P00{number}'
        monkeypatch.setenv('PHARMA_BACKEND','rdflib')
        local=entity_graph(patient)
        monkeypatch.setenv('PHARMA_BACKEND','fuseki')
        remote=entity_graph(patient)
        normalize=lambda rows:sorted(json.dumps(r,sort_keys=True) for r in rows)
        assert normalize(local)==normalize(remote),patient
        assert {v for e in remote for v in (e['s'],e['o']) if '#Patient_' in v}=={str(P[patient])}
        results.append({'graph':patient,'edges':len(remote),'same_answers':True,'patient_isolated':True})
    (ROOT/'validation/fuseki-comparison.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
