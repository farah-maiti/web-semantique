"""TALN français local : spaCy EntityRuler et Matcher, puis gabarits SPARQL.

Ce composant n'est pas un LLM. Il accepte un ensemble documenté d'intentions.
Les cas ambigus ou hors périmètre renvoient une erreur explicite.
"""
import json,re,unicodedata
from functools import lru_cache
import spacy
from spacy.matcher import Matcher
from scripts.build_ontology import ROOT
from .queries import query

EXAMPLES=[
 'Quels médicaments sont contre-indiqués pour le patient P002 ?',
 'Quelles interactions concernent le patient P004 ?',
 'Quels sont les effets secondaires du Glucophage ?',
 'Quels médicaments traitent le diabète de type 2 ?',
 'Quels sont les génériques de Clamoxyl ?',
 'Quels médicaments contiennent de la metformine ?',
 'Quels médicaments sont anti-inflammatoires ?',
 'Combien de médicaments par principe actif ?',
 'Avec quoi interagit la warfarine ?',
 'Liste des médicaments',
]
class UnsupportedQuestion(ValueError):pass

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c)).replace('’',"'").replace('‑','-')

@lru_cache(maxsize=1)
def pipeline():
    data=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf-8'))
    nlp=spacy.blank('fr');ruler=nlp.add_pipe('entity_ruler',config={'phrase_matcher_attr':'LOWER'})
    patterns=[]
    def add(label,key,names):
        for name in set(names):patterns.append({'label':label,'pattern':normalize(name),'id':key})
    for row in data['medicines']:
        names=[row['name'],row['id']]
        if row['id'] in ['Advil_400','Clamoxyl_1g','Glucophage_850','Coumadine_5']:names.append(row['name'].split()[0])
        else:names.append(' '.join(row['name'].split()[:2]))
        add('MEDICAMENT',row['id'],names)
    for row in data['actives']:add('ACTIF',row['id'],[row['id'],row['label']])
    for row in data['conditions']:
        names=[row['id'],row['label']]
        names+= {'DiabeteType2':['diabete','diabete type 2'],'UlcereGastroduodenalEvolutif':['ulcere evolutif'],'AngineStreptococcique':['angine streptococcique']}.get(row['id'],[])
        add('CONDITION',row['id'],names)
    for row in data['patients']:
        pid=row['id'].split('_')[1];add('PATIENT',row['id'],[row['id'],pid,'patient '+pid,'patient '+str(int(pid[1:]))])
    ruler.add_patterns(patterns)
    matcher=Matcher(nlp.vocab)
    vocab={
      'contre_indications':['contre-indique','contre-indiques','contre-indication','contre-indications','contre indique','contre indiques','contre indication','contre indications','alertes','alerte'],
      'interactions':['interaction','interactions','interagit','interagissent'],
      'effets':['effets secondaires','effets indesirables','effet secondaire','effet indesirable'],
      'generiques':['generique','generiques','reference','princeps'],
      'indications':['traitent','traite','indication','indications','pour traiter'],
      'composition':['contient','contiennent','composition','principe actif','principes actifs','molecule','molecules'],
      'classes_inferees':['anti-inflammatoire','anti-inflammatoires','anti inflammatoires','antibiotique','antibiotiques','antidiabetique','antidiabetiques'],
      'statistiques':['combien','nombre'],
    }
    for key,phrases in vocab.items():matcher.add(key,[[{'LOWER':tok.text} for tok in nlp.make_doc(p)] for p in phrases])
    return nlp,matcher

def translate(question):
    if not isinstance(question,str) or not question.strip() or len(question)>500:raise UnsupportedQuestion('Saisissez une question de 1 à 500 caractères.')
    text=normalize(question.strip())
    if re.search(r'\b(sans|sauf|pas|aucun|exclure|moins|plus|superieur|inferieur|dose|posologie|recommande|conseille|enceinte|grossesse|enfant)\b',text):
        raise UnsupportedQuestion('Cette négation, comparaison ou demande clinique dépasse les intentions prises en charge. Choisissez un exemple et précisez une entité du corpus.')
    nlp,matcher=pipeline();doc=nlp(text)
    ents={}
    for ent in doc.ents:ents.setdefault(ent.label_,set()).add(ent.ent_id_)
    if any(len(v)>1 for v in ents.values()):raise UnsupportedQuestion('Plusieurs entités du même type détectées. Posez une question pour une seule entité à la fois.')
    # Reject an unknown patient even if another entity was recognized.
    patient_tokens=re.findall(r'\bp\d+\b',text)
    if patient_tokens and 'PATIENT' not in ents:raise UnsupportedQuestion('Patient inconnu. Le corpus contient P001 à P005.')
    matches=matcher(doc)
    covered={i for ent in doc.ents for i in range(ent.start,ent.end)}
    covered.update(i for _,start,end in matches for i in range(start,end))
    stopwords={"quel","quels","quelle","quelles","qui","de","du","des","la","le","les","l'","d'","un","une","en","dans","ce","cette","sont","est","pour","a","au","aux","avec","quoi","et","par","liste","tous","medicaments","medicament","patient","patients","concerne","concernent"}
    unknown=[token.text for i,token in enumerate(doc) if i not in covered and not token.is_punct and not token.is_space and token.text not in stopwords]
    if unknown:raise UnsupportedQuestion('Terme ou formulation hors du vocabulaire contrôlé : '+', '.join(sorted(set(unknown)))+'. Consultez les exemples.')
    keys={nlp.vocab.strings[m] for m,_,_ in matches}
    filters=[];intent=None
    entity=lambda kind:next(iter(ents[kind]))
    def eq(var,kind):filters.append(f'FILTER(?{var} = po:{entity(kind)})')
    if keys=={'statistiques','composition'} or keys=={'statistiques'}:
        if ents:raise UnsupportedQuestion('Le comptage disponible porte sur tous les médicaments, par principe actif.')
        intent='statistiques'
    elif keys=={'contre_indications'}:
        if 'PATIENT' not in ents:raise UnsupportedQuestion('Précisez un patient fictif, par exemple P002.')
        intent='contre_indications';eq('patient','PATIENT')
        if 'MEDICAMENT' in ents:eq('medicament','MEDICAMENT')
        if set(ents)-{'PATIENT','MEDICAMENT'}:raise UnsupportedQuestion('Cette combinaison d’entités ne correspond pas au scénario de contre-indication.')
    elif keys=={'interactions'}:
        if set(ents)=={'PATIENT'}:intent='interactions_patient';eq('patient','PATIENT')
        elif set(ents)=={'ACTIF'}:intent='interactions_molecules';eq('actif','ACTIF')
        else:raise UnsupportedQuestion('Précisez un patient, ou une substance active comme la warfarine.')
    elif keys=={'effets'}:
        if set(ents)!={'MEDICAMENT'}:raise UnsupportedQuestion('Précisez une spécialité, par exemple Glucophage ou Metformine BGR.')
        intent='effets';eq('medicament','MEDICAMENT')
    elif keys=={'generiques'}:
        if set(ents)!={'MEDICAMENT'}:raise UnsupportedQuestion('Précisez une spécialité de référence, par exemple Clamoxyl.')
        intent='generiques';filters.append(f'FILTER(?reference = po:{entity("MEDICAMENT")} || ?generique = po:{entity("MEDICAMENT")})')
    elif keys=={'indications'}:
        intent='indications'
        if set(ents)=={'CONDITION'}:eq('condition','CONDITION')
        elif set(ents)=={'MEDICAMENT'}:eq('medicament','MEDICAMENT')
        else:raise UnsupportedQuestion('Précisez une spécialité ou une indication du corpus.')
    elif keys=={'composition'}:
        intent='composition'
        if set(ents)=={'ACTIF'}:eq('actif','ACTIF')
        elif set(ents)=={'MEDICAMENT'}:eq('medicament','MEDICAMENT')
        else:raise UnsupportedQuestion('Précisez une spécialité ou une substance active du corpus.')
    elif keys=={'classes_inferees'} and not ents:
        class_mentions=sum(bool(re.search(pattern,text)) for pattern in [r'anti[- ]inflammatoire',r'antibiot',r'antidiabet'])
        if class_mentions!=1:raise UnsupportedQuestion('Précisez une seule classe de médicaments à la fois.')
        intent='classes_inferees'
        options=[('anti','MedicamentAntiInflammatoire'),('antibiot','MedicamentAntibiotique'),('antidiabet','MedicamentAntidiabetique')]
        if 'antibiot' in text:klass=options[1][1]
        elif 'antidiabet' in text:klass=options[2][1]
        else:klass=options[0][1]
        filters.append(f'FILTER(?classe = po:{klass})')
    elif not keys and not ents and re.fullmatch(r'(liste (des |de |de tous les )?medicaments|tous les medicaments|quels sont les medicaments)[ ?.]*',text):intent='catalogue'
    else:raise UnsupportedQuestion('Question non reconnue ou ambiguë. Utilisez une intention proposée et une entité du corpus.')
    return {'intent':intent,'entities':{k:sorted(v) for k,v in ents.items()},'sparql':query(intent,'\n '.join(filters)),'nlp':'spaCy français, règles lexicales et reconnaissance d’entités'}
