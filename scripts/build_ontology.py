"""Construit le schéma OWL, importe le corpus JSON, exporte RDF/XML et Turtle.

Les données sont relues à chaque exécution. Aucun résultat d'inférence n'est
injecté dans le graphe source. Exécuter depuis la racine : python -m scripts.build_ontology.
"""
from pathlib import Path
import json
from decimal import Decimal
from rdflib import Graph, Namespace, URIRef, BNode, Literal, RDF, RDFS, OWL, XSD
from rdflib.collection import Collection

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://www.esprit.tn/pharmaonto'
P = Namespace(BASE+'#')
DCT = Namespace('http://purl.org/dc/terms/')
SWRL = Namespace('http://www.w3.org/2003/11/swrl#')


def build():
    g = Graph()
    for prefix, ns in [('po',P),('owl',OWL),('rdfs',RDFS),('xsd',XSD),('dcterms',DCT),('swrl',SWRL)]:
        g.bind(prefix,ns)
    onto=URIRef(BASE)
    g.add((onto,RDF.type,OWL.Ontology))
    g.add((onto,OWL.versionInfo,Literal('3.0.0')))
    g.add((onto,RDFS.label,Literal('PharmaOnto',lang='fr')))
    g.add((onto,RDFS.comment,Literal('Projet pédagogique Web Sémantique, ESPRIT 5 TWIN 2026-2027. Corpus partiel français, patients fictifs. Les alertes illustrent le raisonnement et ne constituent pas un avis médical.',lang='fr')))
    for name in ['Ahmed Saidani','Fedi Ben Khalifa','Farah Maiti']:
        g.add((onto,DCT.creator,Literal(name)))
    for ap in [DCT.source,DCT.creator,DCT.date,P.notePortee,P.donneeFictive]:
        g.add((ap,RDF.type,OWL.AnnotationProperty))

    schema=json.loads((ROOT/'data/taxonomy.json').read_text(encoding='utf-8'))
    classes=schema['classes']
    for key,row in classes.items():
        g.add((P[key],RDF.type,OWL.Class))
        g.add((P[key],RDFS.label,Literal(row['label'],lang='fr')))
        g.add((P[key],RDFS.comment,Literal(row['definition'],lang='fr')))
        for parent in row['parents']:g.add((P[key],RDFS.subClassOf,P[parent]))
        for source in row['sources']:g.add((P[key],DCT.source,URIRef(source)))
    def listnode(values):
        b=BNode();Collection(g,b,values);return b
    def disjoint(names):
        b=BNode();g.add((b,RDF.type,OWL.AllDisjointClasses));g.add((b,OWL.members,listnode([P[x] for x in names])))
    disjoint([k for k,v in classes.items() if not v['parents']])
    for names in [('Princeps','Generique'),('SurOrdonnance','SansOrdonnance'),('Adulte','Enfant'),('CIAbsolue','CIRelative'),('ObservationFrequente','ObservationTresFrequente','ObservationRare','ObservationTresRare','ObservationPeuFrequente','ObservationFrequenceNonQuantifiee')]:disjoint(names)

    objects = [
        ('aFormePharmaceutique','Medicament','FormePharmaceutique','a pour forme pharmaceutique',OWL.FunctionalProperty),
        ('aVoieAdministration','Medicament','VoieAdministration','a pour voie d’administration',None),
        ('estPrincipeActifDe','PrincipeActif','Medicament','est principe actif de',None),
        ('estPrisPar','Medicament','Patient','est pris par',None),
        ('contientPrincipeActif','Medicament','PrincipeActif','contient le principe actif',None),
        ('traite','Medicament','Pathologie','a une indication documentée pour',None),
        ('estTraitePar','Pathologie','Medicament','a pour médicament indiqué',None),
        ('provoque','Medicament','EffetSecondaire','peut provoquer',None),
        ('aPourContreIndication','Medicament','ContreIndication','a pour contre-indication',None),
        ('concerne','ContreIndication','Pathologie','concerne l’état clinique',None),
        ('interagitAvec','PrincipeActif','PrincipeActif','interaction documentée avec',OWL.SymmetricProperty),
        ('estGeneriqueDe','Generique','Princeps','est générique de',OWL.FunctionalProperty),
        ('souffreDe','Patient','Pathologie','présente l’état clinique',None),
        ('prend','Patient','Medicament','prend dans le scénario',None),
        ('estContreIndiquePour','Medicament','Patient','alerte de contre-indication pour',None),
        ('aObservationEffet','Medicament','ObservationEffet','a une association avec un effet',None),
        ('effetObserve','ObservationEffet','EffetSecondaire','effet associé',OWL.FunctionalProperty),
        ('observationDe','ObservationEffet','Medicament','spécialité concernée',OWL.FunctionalProperty),
        ('interactionMedicamenteuseAvec','Medicament','Medicament','interaction entre spécialités',OWL.SymmetricProperty),
    ]
    for key,dom,rng,label,characteristic in objects:
        g.add((P[key],RDF.type,OWL.ObjectProperty));g.add((P[key],RDFS.domain,P[dom]));g.add((P[key],RDFS.range,P[rng]));g.add((P[key],RDFS.label,Literal(label,lang='fr')))
        if characteristic:g.add((P[key],RDF.type,characteristic))
    g.add((P.traite,OWL.inverseOf,P.estTraitePar));g.add((P.aObservationEffet,OWL.inverseOf,P.observationDe))
    g.add((P.contientPrincipeActif,OWL.inverseOf,P.estPrincipeActifDe))
    g.add((P.prend,OWL.inverseOf,P.estPrisPar))
    g.add((P.provoque,OWL.propertyChainAxiom,listnode([P.aObservationEffet,P.effetObserve])))
    datatypes=[
        ('nomCommercial','Medicament',XSD.string,'nom de la spécialité'),
        ('dosageMg','Medicament',XSD.decimal,'masse par unité en mg'),
        ('substanceDosee','Medicament',XSD.string,'substance correspondant à la masse'),
        ('formeGalenique','Medicament',XSD.string,'forme galénique'),
        ('codeCIS','Medicament',XSD.string,'code CIS français'),
        ('frequence','ObservationEffet',XSD.string,'fréquence pour cette spécialité'),
        ('description','ContreIndication',XSD.string,'description de la condition'),
        ('age','Patient',XSD.integer,'âge fictif en années'),
    ]
    for key,dom,dt,label in datatypes:
        g.add((P[key],RDF.type,OWL.DatatypeProperty));g.add((P[key],RDF.type,OWL.FunctionalProperty));g.add((P[key],RDFS.domain,P[dom]));g.add((P[key],RDFS.range,dt));g.add((P[key],RDFS.label,Literal(label,lang='fr')))
    def restriction(prop,kind,value,onclass=None):
        b=BNode();g.add((b,RDF.type,OWL.Restriction));g.add((b,OWL.onProperty,P[prop]));g.add((b,kind,value))
        if onclass:g.add((b,OWL.onClass,P[onclass]))
        return b
    g.add((P.Generique,RDFS.subClassOf,restriction('estGeneriqueDe',OWL.qualifiedCardinality,Literal(1,datatype=XSD.nonNegativeInteger),'Princeps')))
    g.add((P.Medicament,RDFS.subClassOf,restriction('contientPrincipeActif',OWL.someValuesFrom,P.PrincipeActif)))
    def equivalent(key,parts):
        b=BNode();g.add((b,RDF.type,OWL.Class));g.add((b,OWL.intersectionOf,listnode(parts)))
        g.add((P[key],OWL.equivalentClass,b))
    for key,row in classes.items():
        if row.get('equivalent_some'):
            d=row['equivalent_some']
            equivalent(key,[P[d['base']],restriction(d['property'],OWL.someValuesFrom,P[d['filler']])])
        if row.get('age_range'):
            lo,hi=row['age_range'];dt=BNode();g.add((dt,RDF.type,RDFS.Datatype));g.add((dt,OWL.onDatatype,XSD.integer))
            facets=[]
            for kind,value in [(XSD.minInclusive,lo),(XSD.maxInclusive,hi)]:
                if value is not None:
                    facet=BNode();g.add((facet,kind,Literal(value,datatype=XSD.integer)));facets.append(facet)
            g.add((dt,OWL.withRestrictions,listnode(facets)))
            equivalent(key,[P.Patient,restriction('age',OWL.someValuesFrom,dt)])
        if row.get('min_takes'):
            equivalent(key,[P.Patient,restriction('prend',OWL.minQualifiedCardinality,Literal(row['min_takes'],datatype=XSD.nonNegativeInteger),'Medicament')])
    for group in [('AdulteJeune','AdulteMoyenAge','PersonneAgee'),('Adolescent','JeuneEnfant')]:disjoint(group)
    g.add((P.Medicament,RDFS.subClassOf,restriction('aFormePharmaceutique',OWL.qualifiedCardinality,Literal(1,datatype=XSD.nonNegativeInteger),'FormePharmaceutique')))
    g.add((P.Medicament,RDFS.subClassOf,restriction('aVoieAdministration',OWL.someValuesFrom,P.VoieAdministration)))

    data=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf-8'))
    def individual(key,types,label,source=None,fake=False):
        g.add((P[key],RDF.type,OWL.NamedIndividual));g.add((P[key],RDFS.label,Literal(label,lang='fr')))
        for ty in types:g.add((P[key],RDF.type,P[ty]))
        if source:
            g.add((P[key],DCT.source,URIRef(source)));g.add((P[key],DCT.date,Literal(data['consulted'],datatype=XSD.date)))
        if fake:g.add((P[key],P.donneeFictive,Literal(True)))
    for row in data['actives']:
        individual(row['id'],row['classes'],row['label'],row['source'])
        g.add((P[row['id']],DCT.source,URIRef(row['classification_source'])))
    for row in data['conditions']:individual(row['id'],row['classes'],row['label'],row.get('source'))
    for row in data['effects']:individual(row['id'],row['classes'],row['label'])
    for row in data['contraindications']:
        individual(row['id'],[row['class']],row['label'],row['source'])
        g.add((P[row['id']],P.concerne,P[row['condition']]))
        g.add((P[row['id']],P.description,Literal(row['label'],datatype=XSD.string)))
    for row in data['forms']+data['routes']:individual(row['id'],[row['class']],row['label'])
    for row in data['medicines']:
        s=P[row['id']];individual(row['id'],row['classes'],row['name'],row['source'])
        for key,field,dt in [('nomCommercial','name',XSD.string),('dosageMg','strength_mg',XSD.decimal),('substanceDosee','strength_substance',XSD.string),('formeGalenique','form',XSD.string),('codeCIS','cis',XSD.string)]:
            value=Decimal(row[field]).quantize(Decimal('0.0')) if dt==XSD.decimal else row[field]
            g.add((s,P[key],Literal(value,datatype=dt)))
        g.add((s,P.contientPrincipeActif,P[row['active']]))
        g.add((s,P.aFormePharmaceutique,P[row['form_id']]))
        g.add((s,P.aVoieAdministration,P[row['route_id']]))
        for field,prop in [('indications','traite'),('contraindications','aPourContreIndication')]:
            for value in row[field]:g.add((s,P[prop],P[value]))
        if row.get('reference'):g.add((s,P.estGeneriqueDe,P[row['reference']]))
        if row.get('scope'):g.add((s,P.notePortee,Literal(row['scope'],lang='fr')))
    for row in data['observations']:
        s=P[row['id']];individual(row['id'],row['classes'],row['label'],row['source'])
        g.add((s,P.observationDe,P[row['medicine']]))
        g.add((s,P.effetObserve,P[row['effect']]))
        g.add((s,P.frequence,Literal(row['frequency'],datatype=XSD.string)))
    for row in data['interactions']:
        triple=(P[row['a']],P.interagitAvec,P[row['b']]);g.add(triple)
        ax=BNode();g.add((ax,RDF.type,OWL.Axiom));g.add((ax,OWL.annotatedSource,triple[0]));g.add((ax,OWL.annotatedProperty,triple[1]));g.add((ax,OWL.annotatedTarget,triple[2]));g.add((ax,DCT.source,URIRef(row['source'])))
    for row in data['patients']:
        individual(row['id'],row['classes'],row['label'],fake=True)
        g.add((P[row['id']],P.age,Literal(row['age'],datatype=XSD.integer)))
        for med in row['medicines']:g.add((P[row['id']],P.prend,P[med]))
        for condition in row['conditions']:g.add((P[row['id']],P.souffreDe,P[condition]))
    distinct=BNode();g.add((distinct,RDF.type,OWL.AllDifferent));g.add((distinct,OWL.distinctMembers,listnode(sorted(g.subjects(RDF.type,OWL.NamedIndividual),key=str))))
    # Pure OWL 2 DL file. SWRL extension is exported separately, self-contained.
    g.serialize(ROOT/'ontology/pharmaonto.owl',format='xml')
    g.serialize(ROOT/'ontology/pharmaonto.ttl',format='turtle')
    ext=Graph();ext+=g
    for pre,ns in g.namespaces():ext.bind(pre,ns)
    def variable(name):
        v=URIRef('urn:swrl:var#'+name);ext.add((v,RDF.type,SWRL.Variable));return v
    def atom(kind,predicate,a,b=None):
        node=BNode();ext.add((node,RDF.type,SWRL[kind]));ext.add((node,SWRL.classPredicate if kind=='ClassAtom' else SWRL.propertyPredicate,P[predicate]));ext.add((node,SWRL.argument1,variable(a)))
        if b:ext.add((node,SWRL.argument2,variable(b)))
        return node
    rule=P.RegleContreIndication
    ext.add((rule,RDF.type,SWRL.Imp));ext.add((rule,RDFS.label,Literal('Alerte de contre-indication absolue pour une prise connue',lang='fr')))
    body=[atom('ClassAtom','Patient','p'),atom('IndividualPropertyAtom','prend','p','m'),atom('IndividualPropertyAtom','aPourContreIndication','m','ci'),atom('ClassAtom','CIAbsolue','ci'),atom('IndividualPropertyAtom','concerne','ci','c'),atom('IndividualPropertyAtom','souffreDe','p','c')]
    for prop,atoms in [(SWRL.body,body),(SWRL.head,[atom('IndividualPropertyAtom','estContreIndiquePour','m','p')])]:
        node=BNode();Collection(ext,node,atoms);ext.add((rule,prop,node))
    ext.serialize(ROOT/'ontology/pharmaonto-swrl.owl',format='xml')
    def depth(key):return 1+max((depth(p) for p in classes[key]['parents']),default=0)
    counts={'version':schema['version'],'max_hierarchy_depth':max(map(depth,classes)),'root_classes':sum(not r['parents'] for r in classes.values()),'defined_classes':sum(bool(r.get('equivalent_some') or r.get('age_range') or r.get('min_takes')) for r in classes.values()),'classes':len(classes),'object_properties':len(objects),'data_properties':len(datatypes),'individuals':len(set(g.subjects(RDF.type,OWL.NamedIndividual))),'asserted_triples':len(g),'medicines':len(data['medicines']),'patients':len(data['patients'])}
    (ROOT/'validation/counts.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
    print(json.dumps(counts))
    return g

if __name__=='__main__':build()
