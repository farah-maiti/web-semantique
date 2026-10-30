"""Read-only views of the actual OWL graph and the selected SPARQL backend."""
import json
from functools import lru_cache
from rdflib import Graph, RDF, RDFS, OWL, URIRef
from rdflib.collection import Collection
from scripts.build_ontology import ROOT, P, DCT
from .semantic import execute, rows


@lru_cache(maxsize=1)
def schema_graph():
    return Graph().parse(ROOT/'ontology/pharmaonto.owl')


def label(graph, term):
    return str(graph.value(term, RDFS.label) or str(term).split('#')[-1])


def expression(graph, term):
    if isinstance(term, URIRef):return label(graph, term)
    conjunction=graph.value(term,OWL.intersectionOf)
    if conjunction:return ' ET '.join(expression(graph,x) for x in Collection(graph,conjunction))
    prop=graph.value(term,OWL.onProperty)
    some=graph.value(term,OWL.someValuesFrom)
    if prop and some:return f"{label(graph,prop)} AU MOINS UN ({expression(graph,some)})"
    for predicate,word in [(OWL.qualifiedCardinality,'EXACTEMENT'),(OWL.minQualifiedCardinality,'AU MOINS')]:
        count=graph.value(term,predicate)
        if prop and count is not None:return f"{label(graph,prop)} {word} {count} ({expression(graph,graph.value(term,OWL.onClass))})"
    restrictions=graph.value(term,OWL.withRestrictions)
    if restrictions:
        bounds=[]
        for facet in Collection(graph,restrictions):
            for predicate,value in graph.predicate_objects(facet):
                bounds.append(('≥' if str(predicate).endswith('minInclusive') else '≤')+' '+str(value))
        return 'entier '+', '.join(bounds)
    return 'Expression OWL'


def ontology_snapshot():
    graph=schema_graph()
    memberships=rows(execute('''PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?individual ?class WHERE {
      ?individual a owl:NamedIndividual, ?class . ?class a owl:Class .
      FILTER(isIRI(?class))
    }'''))
    members={}
    for row in memberships:
        term=URIRef(row['individual']);klass=URIRef(row['class'])
        members.setdefault(str(klass),[]).append({'id':str(term).split('#')[-1],'label':label(graph,term),'asserted':(term,RDF.type,klass) in graph})
    classes=[]
    for term in sorted(set(graph.subjects(RDF.type,OWL.Class)),key=str):
        if not isinstance(term,URIRef) or not str(term).startswith(str(P)):continue
        parents=[str(p).split('#')[-1] for p in graph.objects(term,RDFS.subClassOf) if isinstance(p,URIRef)]
        equivalents=[expression(graph,e) for e in graph.objects(term,OWL.equivalentClass)]
        constraints=[expression(graph,e) for e in graph.objects(term,RDFS.subClassOf) if not isinstance(e,URIRef)]
        classes.append({'id':str(term).split('#')[-1],'iri':str(term),'label':label(graph,term),
            'definition':str(graph.value(term,RDFS.comment) or ''),'parents':sorted(parents),
            'equivalents':equivalents,'constraints':constraints,
            'sources':sorted(str(s) for s in graph.objects(term,DCT.source)),
            'members':sorted(members.get(str(term),[]),key=lambda x:x['label'])})
    return {'classes':classes,'counts':json.loads((ROOT/'validation/counts.json').read_text()),'origin':'ontology/pharmaonto.owl','members_origin':'graphe matérialisé interrogé via SPARQL'}


def medicine_detail(identifier):
    corpus=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf-8'))
    medicine=next((m for m in corpus['medicines'] if m['id']==identifier),None)
    if medicine is None:raise ValueError('Spécialité inconnue')
    graph=schema_graph()
    # The only interpolated identifier was selected from the fixed local corpus.
    memberships=rows(execute('''PREFIX po: <http://www.esprit.tn/pharmaonto#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?class WHERE { po:__ID__ a ?class . ?class a owl:Class . FILTER(isIRI(?class)) }'''.replace('__ID__',identifier)))
    classes=[{'id':r['class'].split('#')[-1],'label':label(graph,URIRef(r['class'])),'asserted':(P[identifier],RDF.type,URIRef(r['class'])) in graph} for r in memberships]
    by_id=lambda collection:{x['id']:x for x in corpus[collection]}
    active=by_id('actives')[medicine['active']]
    return {'medicine':medicine,'active':active,'classes':sorted(classes,key=lambda c:c['label']),
        'indications':[by_id('conditions')[i] for i in medicine['indications']],
        'contraindications':[by_id('contraindications')[i] for i in medicine['contraindications']],
        'effects':[dict(o,effect_label=by_id('effects')[o['effect']]['label']) for o in corpus['observations'] if o['medicine']==identifier],
        'reference':by_id('medicines').get(medicine.get('reference')),
        'route':by_id('routes')[medicine['route_id']]['label'],'consulted':corpus['consulted']}
