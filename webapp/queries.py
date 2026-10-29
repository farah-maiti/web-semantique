"""SPARQL SELECT autorisées. Les paramètres sont des identifiants du corpus."""
PREFIX='''PREFIX po: <http://www.esprit.tn/pharmaonto#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct: <http://purl.org/dc/terms/>
'''
QUERIES={
'catalogue':('Catalogue des spécialités', '''SELECT ?medicament ?nom ?dosage ?substanceDosee ?forme ?molecule ?source WHERE {
 ?medicament a po:Medicament ; po:nomCommercial ?nom ; po:dosageMg ?dosage ;
 po:substanceDosee ?substanceDosee ; po:formeGalenique ?forme ; po:contientPrincipeActif ?a ; dct:source ?source .
 ?a rdfs:label ?molecule . } ORDER BY ?nom'''),
'patients':('Patients fictifs et prises', '''SELECT ?patient ?nom ?age (GROUP_CONCAT(DISTINCT ?med; separator=", ") AS ?medicaments) WHERE {
 ?patient a po:Patient ; rdfs:label ?nom ; po:age ?age .
 OPTIONAL { ?patient po:prend/po:nomCommercial ?med . }
 } GROUP BY ?patient ?nom ?age ORDER BY ?patient'''),
'contre_indications':('Alertes de contre-indication avec justification', '''SELECT DISTINCT ?patient ?medicament ?nom ?condition ?motif ?source WHERE {
 ?medicament po:estContreIndiquePour ?patient ; po:nomCommercial ?nom ;
 po:aPourContreIndication ?ci .
 ?patient po:prend ?medicament ; po:souffreDe ?condition .
 ?ci a po:CIAbsolue ; po:concerne ?condition ; po:description ?motif ; dct:source ?source .
 __FILTER__
 } ORDER BY ?patient ?nom'''),
'interactions_patient':('Co-prises avec interaction documentée', '''SELECT DISTINCT ?patient ?medicament1 ?nom1 ?medicament2 ?nom2 ?source WHERE {
 ?patient a po:Patient ; po:prend ?medicament1, ?medicament2 .
 ?medicament1 po:interactionMedicamenteuseAvec ?medicament2 ; po:nomCommercial ?nom1 ; dct:source ?source .
 ?medicament2 po:nomCommercial ?nom2 .
 FILTER(STR(?medicament1) < STR(?medicament2))
 __FILTER__
 } ORDER BY ?patient ?nom1'''),
'effets':('Effets possibles et fréquence par spécialité', '''SELECT ?medicament ?nom ?effet ?frequence ?source WHERE {
 ?observation a po:ObservationEffet ; po:observationDe ?medicament ; po:effetObserve/rdfs:label ?effet ; po:frequence ?frequence ; dct:source ?source .
 ?medicament po:nomCommercial ?nom . __FILTER__
 } ORDER BY ?nom ?effet'''),
'generiques':('Génériques et références', '''SELECT ?generique ?nom ?reference ?nomReference ?source WHERE {
 ?generique a po:Generique ; po:nomCommercial ?nom ; po:estGeneriqueDe ?reference ; dct:source ?source .
 ?reference po:nomCommercial ?nomReference . __FILTER__
 } ORDER BY ?nom'''),
'indications':('Indications documentées', '''SELECT ?medicament ?nom ?condition ?indication ?source WHERE {
 ?medicament po:traite ?condition ; po:nomCommercial ?nom ; dct:source ?source .
 ?condition rdfs:label ?indication . __FILTER__
 } ORDER BY ?nom'''),
'composition':('Composition et masse par unité', '''SELECT ?medicament ?nom ?molecule ?dosage ?substanceDosee ?source WHERE {
 ?medicament po:contientPrincipeActif ?actif ; po:nomCommercial ?nom ; po:dosageMg ?dosage ; po:substanceDosee ?substanceDosee ; dct:source ?source .
 ?actif rdfs:label ?molecule . __FILTER__
 } ORDER BY ?nom'''),
'classes_inferees':('Classification sémantique des médicaments', '''SELECT ?medicament ?nom ?classe ?libelle WHERE {
 VALUES ?classe { po:MedicamentAntiInflammatoire po:MedicamentAntibiotique po:MedicamentAntidiabetique }
 ?medicament a ?classe ; po:nomCommercial ?nom . ?classe rdfs:label ?libelle . __FILTER__
 } ORDER BY ?nom'''),
'interactions_molecules':('Interactions entre substances', '''SELECT ?actif ?nom ?autre ?nomAutre WHERE {
 ?actif po:interagitAvec ?autre ; rdfs:label ?nom . ?autre rdfs:label ?nomAutre . __FILTER__
 } ORDER BY ?nom'''),
'statistiques':('Nombre de spécialités par principe actif', '''SELECT ?molecule (COUNT(DISTINCT ?medicament) AS ?nombre) WHERE {
 ?medicament a po:Medicament ; po:contientPrincipeActif/rdfs:label ?molecule .
 } GROUP BY ?molecule ORDER BY DESC(?nombre) ?molecule'''),
'inverse':('Relation inverse déduite', '''SELECT ?condition ?indication ?medicament ?nom WHERE {
 ?condition po:estTraitePar ?medicament ; rdfs:label ?indication .
 ?medicament po:nomCommercial ?nom . } ORDER BY ?indication ?nom'''),
}

def query(key,filters=''):
    return PREFIX+QUERIES[key][1].replace('__FILTER__',filters)+'\nLIMIT 200'

def export_queries():
    from scripts.build_ontology import ROOT
    for index,(key,(label,_)) in enumerate(QUERIES.items(),1):
        (ROOT/'queries'/f'Q{index:02}_{key}.rq').write_text('# '+label+'\n'+query(key),encoding='utf-8')

if __name__=='__main__':export_queries()
