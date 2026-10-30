"""Regression checks for deep classifications, boundaries and explorer data."""
import json
import pytest
from rdflib import Graph, RDF, RDFS, OWL, XSD, Literal, URIRef
from pyshacl import validate
from scripts.build_ontology import ROOT, P
from scripts.reason import check
from webapp.explorer import ontology_snapshot, medicine_detail

@pytest.fixture(scope='module')
def source():return Graph().parse(ROOT/'ontology/pharmaonto.owl')

@pytest.fixture(scope='module')
def inferred():return Graph().parse(ROOT/'ontology/pharmaonto-materialized.ttl',format='turtle')

@pytest.mark.parametrize('individual,klass',[
 ('Amoxicilline','AntiInfectieux'),('Amoxicilline','Penicilline'),
 ('Clamoxyl_1g','MedicamentPenicillineLargeSpectre'),
 ('Amoxicilline_BGR_1g','MedicamentBetaLactamine'),
 ('Advil_400','MedicamentDerivePropionique'),('Coumadine_5','MedicamentAntivitamineK'),
 ('Glucophage_850','MedicamentBiguanide'),('Metformine_BGR_850','MedicamentComprimeEnrobe'),
 ('Glucophage_850','MedicamentComprimePellicule'),('Clamoxyl_1g','MedicamentComprimeDispersible'),
 ('Patient_P001','AdulteMoyenAge'),('Patient_P003','AdulteJeune'),
 ('Patient_P004','PatientAvecPlusieursMedicaments'),('Patient_P001','PatientAvecMaladieChronique'),
 ('CI_UlcereEvolutif','CIDigestive'),('CI_AllergiePenicillines','CIHypersensibilite'),
 ('CI_InsuffisanceRenaleSevere','CIRenale')])
def test_specific_classifications_are_derived(source,inferred,individual,klass):
    triple=(P[individual],RDF.type,P[klass])
    assert triple not in source
    assert triple in inferred

def test_hierarchy_has_no_named_cycles_or_punning(source):
    assert not list(source.query('SELECT ?c WHERE { ?c <http://www.w3.org/2000/01/rdf-schema#subClassOf>+ ?c . FILTER(isIRI(?c)) }'))
    classes={s for s in source.subjects(RDF.type,OWL.Class) if isinstance(s,URIRef)}
    assert not classes.intersection(source.subjects(RDF.type,OWL.NamedIndividual))
    for c in classes:
        assert source.value(c,RDFS.label) and source.value(c,RDFS.comment)
    leaf=P.PenicillineLargeSpectre
    path=[]
    while leaf is not None:
        path.append(leaf)
        leaf=next((p for p in source.objects(leaf,RDFS.subClassOf) if isinstance(p,URIRef)),None)
    assert path==[P.PenicillineLargeSpectre,P.Penicilline,P.BetaLactamine,P.Antibiotique,P.Antibacterien,P.AntiInfectieux,P.PrincipeActif]

def test_age_boundary_inferences(source,tmp_path):
    g=Graph();g+=source
    expected={0:'JeuneEnfant',11:'JeuneEnfant',12:'Adolescent',17:'Adolescent',18:'AdulteJeune',44:'AdulteJeune',45:'AdulteMoyenAge',64:'AdulteMoyenAge',65:'PersonneAgee',79:'PersonneAgee',80:'PersonneTresAgee'}
    for age in expected:
        individual=P['AgeProbe_'+str(age)];g.add((individual,RDF.type,OWL.NamedIndividual));g.add((individual,RDF.type,P.Patient));g.add((individual,P.age,Literal(age,datatype=XSD.integer)))
    file=tmp_path/'ages.owl';g.serialize(file,format='xml');result=tmp_path/'ages.nt'
    checked=check(file,result);assert checked.returncode==0,checked.stdout
    entailed=Graph().parse(result,format='nt')
    for age,klass in expected.items():assert (P['AgeProbe_'+str(age)],RDF.type,P[klass]) in entailed

@pytest.mark.parametrize('fault',['missing_form','missing_route','wrong_form_type'])
def test_extended_shacl_requirements(source,fault):
    g=Graph();g+=source
    if fault=='missing_form':g.remove((P.Advil_400,P.aFormePharmaceutique,None))
    elif fault=='missing_route':g.remove((P.Advil_400,P.aVoieAdministration,None))
    else:
        # A range axiom can infer a class, but cannot invent the missing label.
        g.set((P.Advil_400,P.aFormePharmaceutique,P.UnknownForm))
    assert not validate(g,shacl_graph=str(ROOT/'ontology/shapes.ttl'),inference='rdfs')[0]

def test_form_and_active_inverses(inferred):
    assert (P.Ibuprofene,P.estPrincipeActifDe,P.Advil_400) in inferred
    assert (P.Advil_400,P.estPrisPar,P.Patient_P002) in inferred
    assert (P.Patient_P002,RDF.type,P.PatientAvecPlusieursMedicaments) not in inferred

def test_explorer_distinguishes_asserted_membership(monkeypatch):
    monkeypatch.setenv('PHARMA_BACKEND','rdflib')
    result=ontology_snapshot();classes={c['id']:c for c in result['classes']}
    assert len(classes)==result['counts']['classes']==105
    assert classes['PenicillineLargeSpectre']['members']==[{'id':'Amoxicilline','label':'Amoxicilline','asserted':True}]
    assert classes['Penicilline']['members'][0]['asserted'] is False
    assert classes['MedicamentPenicillineLargeSpectre']['equivalents']
    assert {m['id'] for m in classes['MedicamentPenicillineLargeSpectre']['members']}=={'Clamoxyl_1g','Amoxicilline_BGR_1g'}

def test_medicine_dossier_matches_source(monkeypatch):
    monkeypatch.setenv('PHARMA_BACKEND','rdflib')
    data=medicine_detail('Glucophage_850')
    assert data['medicine']['strength_substance']=='chlorhydrate de metformine'
    assert data['route']=='voie orale'
    assert len(data['effects'])==2
    assert 'MedicamentBiguanide' in {c['id'] for c in data['classes'] if not c['asserted']}
    with pytest.raises(ValueError):medicine_detail('Glucophage_850 } UNION { ?s ?p ?o }')

def test_new_endpoints(monkeypatch):
    monkeypatch.setenv('PHARMA_BACKEND','rdflib')
    import os,django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','webapp.settings');django.setup()
    from django.test import Client
    client=Client()
    assert client.get('/api/ontology').json()['counts']['max_hierarchy_depth']==7
    assert client.get('/api/medicine/Advil_400').json()['medicine']['cis']=='63646874'
    assert client.get('/api/medicine/Unknown').status_code==404
    response=client.get('/download/owl');assert response.status_code==200
    assert b'3.0.0' in b''.join(response.streaming_content)
    assert client.get('/download/requirements.txt').status_code==404
