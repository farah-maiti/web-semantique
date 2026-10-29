"""Vérification HermiT et export explicite des faits inférés pour Fuseki."""
from pathlib import Path
import subprocess, os, json, hashlib
import owlready2
from rdflib import Graph, RDF, OWL
from .build_ontology import ROOT,P


def java_paths():
    folder=Path(owlready2.__file__).parent/'hermit'
    jar=folder/'HermiT.jar'
    target=ROOT/'runtime/java'
    target.mkdir(parents=True,exist_ok=True)
    java_home=os.environ.get('JAVA_HOME')
    java=str(Path(java_home)/'bin/java') if java_home else 'java'
    javac=str(Path(java_home)/'bin/javac') if java_home else 'javac'
    subprocess.run([javac,'-encoding','UTF-8','-cp',str(jar),'-d',str(target),str(ROOT/'scripts/ValidateOntology.java')],check=True,capture_output=True,text=True)
    return java,os.pathsep.join([str(jar),str(target)])


def check(path,output=None):
    java,cp=java_paths()
    command=[java,'-Xmx1G','-cp',cp,'ValidateOntology',str(path)]
    if output:command.append(str(output))
    return subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=120)


def materialize():
    original=ROOT/'ontology/pharmaonto.owl'
    asserted=Graph().parse(original)
    result=check(original,ROOT/'validation/hermit-entailed.nt')
    (ROOT/'validation/hermit.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode or 'owl2dl=true' not in result.stdout:
        raise RuntimeError('Validation OWL 2 DL / HermiT échouée. Voir validation/hermit.log')
    owl=Graph().parse(ROOT/'validation/hermit-entailed.nt',format='nt')
    merged=Graph();merged+=asserted;merged+=owl
    rule_graph=Graph()
    # Equivalent de la règle SWRL, explicité dans un fichier SPARQL CONSTRUCT.
    for query in ['R1_contre_indication.rq','R2_interaction_specialites.rq']:
        new=merged.query((ROOT/'queries'/query).read_text(encoding='utf-8')).graph
        rule_graph+=new;merged+=new
    owl_delta=Graph();owl_delta+=owl-asserted
    rule_graph=rule_graph-asserted-owl
    for graph in [merged,owl_delta,rule_graph]:
        for prefix,ns in asserted.namespaces():graph.bind(prefix,ns)
    owl_delta.serialize(ROOT/'ontology/inferences-owl.ttl',format='turtle')
    rule_graph.serialize(ROOT/'ontology/inferences-regles.ttl',format='turtle')
    merged.serialize(ROOT/'ontology/pharmaonto-materialized.ttl',format='turtle')
    # Check that the separate SWRL file really gives the expected alert in HermiT.
    swrl=check(ROOT/'ontology/pharmaonto-swrl.owl',ROOT/'validation/swrl-entailed.nt')
    (ROOT/'validation/hermit-swrl.log').write_text(swrl.stdout+swrl.stderr,encoding='utf-8')
    if swrl.returncode:raise RuntimeError('Extension SWRL rejetée par HermiT')
    sg=Graph().parse(ROOT/'validation/swrl-entailed.nt',format='nt')
    expected=set(merged.triples((None,P.estContreIndiquePour,None)))
    actual=set(sg.triples((None,P.estContreIndiquePour,None)))
    if actual!=expected:raise AssertionError(('Désaccord SWRL / CONSTRUCT',expected,actual))
    stats=json.loads((ROOT/'validation/counts.json').read_text())
    stats.update(owl_inferred_triples=len(owl_delta),rule_inferred_triples=len(rule_graph),materialized_triples=len(merged),contraindication_alerts=len(expected),source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),swrl_equivalence=True)
    (ROOT/'validation/counts.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    print(json.dumps(stats))
    return merged

if __name__=='__main__':materialize()
