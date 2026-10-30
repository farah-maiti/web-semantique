'use strict';
const $=id=>document.getElementById(id);
let meta=null,loaded=new Set();
const renderedResults=new Map();
let graphRequest=0;
const cellLabels={medicament:'Spécialité',nom:'Nom',dosage:'Masse (mg)',substanceDosee:'Substance dosée',forme:'Forme',molecule:'Substance active',source:'Source',patient:'Patient',condition:'État clinique',motif:'Motif',nom1:'Spécialité 1',nom2:'Spécialité 2',effet:'Effet possible',frequence:'Fréquence',generique:'Générique',reference:'Référence',nomReference:'Nom de référence',indication:'Indication',classe:'Classe',libelle:'Classe',libelleParent:'Classe parente',parent:'Parent',voie:'Voie',autre:'Substance liée',nomAutre:'Substance liée',nombre:'Nombre',age:'Âge',medicaments:'Prises',actif:'Substance',s:'Sujet',p:'Relation',o:'Objet',labelS:'Sujet',labelO:'Objet'};
const short=s=>s.includes('#')?s.split('#').pop():s;
async function api(url,options={}){const r=await fetch(url,options);let data;try{data=await r.json();}catch{throw new Error('Réponse du serveur illisible.');}if(!r.ok)throw new Error(data.error||'La requête a échoué.');return data;}
function table(target,result){renderedResults.set(target,result);const exportId=target==='result-table'?'export-search':target==='workshop-result'?'export-workshop':null;if(exportId)$(exportId).disabled=!(result.results?.bindings?.length);const root=$(target);root.replaceChildren();const bindings=result.results?.bindings||[];if(!bindings.length){const p=document.createElement('p');p.className='empty';p.textContent='Aucun résultat dans le corpus actuel. Cela ne permet pas de conclure à une absence de risque.';root.append(p);return;}const rawVars=result.head.vars;const hide=new Set();if(rawVars.includes('nom'))hide.add('medicament');if(rawVars.includes('nom1'))hide.add('medicament1');if(rawVars.includes('nom2'))hide.add('medicament2');if(rawVars.includes('libelle'))hide.add('classe');if(rawVars.includes('indication'))hide.add('condition');if(rawVars.includes('nomReference')){hide.add('reference');hide.add('generique');}if(rawVars.includes('nomAutre')){hide.add('actif');hide.add('autre');}const vars=rawVars.filter(v=>!hide.has(v));const wrap=document.createElement('div');wrap.className='table-scroll';const t=document.createElement('table');const head=t.createTHead().insertRow();vars.forEach(v=>{const th=document.createElement('th');th.scope='col';th.textContent=cellLabels[v]||v;head.append(th);});const body=t.createTBody();bindings.forEach(row=>{const tr=body.insertRow();vars.forEach(v=>{const td=tr.insertCell();const val=row[v]?.value||'—';if(v==='source'&&val.startsWith('https://base-donnees-publique.medicaments.gouv.fr/')){const a=document.createElement('a');a.href=val;a.textContent='Fiche officielle ↗';a.target='_blank';a.rel='noopener noreferrer';a.className='source-link';td.append(a);}else{td.textContent=short(val);td.title=val;}});});wrap.append(t);root.append(wrap);}
async function loadQuery(id,target){const data=await api('/api/query/'+encodeURIComponent(id));table(target,data.result);return data;}
async function showView(view){document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!=='view-'+view);document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.view===view));$('breadcrumb').textContent=document.querySelector(`[data-view="${view}"]`).textContent.trim();if(loaded.has(view))return;try{if(view==='catalogue')await loadCatalogue();if(view==='ontology')await loadOntology();if(view==='patients')await Promise.all([loadQuery('patients','patients-content'),loadQuery('contre_indications','ci-content'),loadQuery('interactions_patient','interactions-content')]);if(view==='graph')await drawGraph();if(view==='queries')await workshop();loaded.add(view);$('connection-error').hidden=true;}catch(e){$('connection-error').hidden=false;$('connection-error').textContent=e.message;}}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
function csrf(){const cookie=document.cookie.split('; ').find(x=>x.startsWith('csrftoken='));return cookie?decodeURIComponent(cookie.split('=').slice(1).join('=')):'';}
$('ask-form').addEventListener('submit',async event=>{event.preventDefault();$('ask-button').disabled=true;$('search-feedback').textContent='Analyse de la question et interrogation du graphe…';$('search-result').hidden=true;try{const data=await api('/api/ask',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify({question:$('question').value})});table('result-table',data.result);$('query-code').textContent=data.sparql;$('interpretation').textContent='Intention : '+data.intent+' · Entités : '+Object.values(data.entities).flat().join(', ')+' · '+data.nlp;$('result-count').textContent=data.result.results.bindings.length+' résultat(s)';$('search-feedback').textContent=data.message;$('search-result').hidden=false;$('intro').hidden=true;}catch(e){$('search-feedback').textContent=e.message;}finally{$('ask-button').disabled=false;}});
async function workshop(){const data=await loadQuery($('query-select').value,'workshop-result');$('workshop-code').textContent=data.sparql;}
$('run-query').addEventListener('click',async()=>{try{await workshop();}catch(e){$('workshop-result').textContent=e.message;}});
$('query-select').addEventListener('change',async()=>{try{await workshop();}catch(e){$('workshop-result').textContent=e.message;}});
const ns='http://www.w3.org/2000/svg';function svg(tag,attrs,text){const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs||{}))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
async function drawGraph(){const request=++graphRequest;const selectedPatient=$('graph-patient').value;const data=await api('/api/graph?patient='+encodeURIComponent(selectedPatient));if(request!==graphRequest)return;const root=$('graph-svg');root.replaceChildren();const defs=svg('defs');['declared','derived'].forEach((id,i)=>{const mark=svg('marker',{id,markerWidth:9,markerHeight:9,refX:8,refY:4.5,orient:'auto'});mark.append(svg('path',{d:'M0,0 L9,4.5 L0,9 Z',fill:i?'#d77a61':'#8bafa6'}));defs.append(mark);});root.append(defs);const ids=[...new Set(data.edges.flatMap(e=>[e.s,e.o]))];const positions={};const patient='http://www.esprit.tn/pharmaonto#'+selectedPatient;const labels={};data.edges.forEach(e=>{labels[e.s]=e.labelS;labels[e.o]=e.labelO;});let others=ids.filter(i=>i!==patient);positions[patient]=[500,290];others.forEach((id,i)=>{const angle=(i/others.length)*Math.PI*2-Math.PI/2;positions[id]=[500+330*Math.cos(angle),290+215*Math.sin(angle)];});data.edges.forEach((edge,i)=>{const a=positions[edge.s],b=positions[edge.o];const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1;const inferred=/estContreIndiquePour|interactionMedicamenteuseAvec/.test(edge.p);const line=svg('line',{x1:a[0]+dx/len*42,y1:a[1]+dy/len*24,x2:b[0]-dx/len*75,y2:b[1]-dy/len*26,stroke:inferred?'#d77a61':'#9bbdb4','stroke-width':inferred?2:1.5,'marker-end':'url(#'+(inferred?'derived':'declared')+')'});if(inferred)line.setAttribute('stroke-dasharray','6 4');const title=svg('title',{},short(edge.p));line.append(title);root.append(line);const tx=(a[0]+b[0])/2,ty=(a[1]+b[1])/2-7-(i%2)*5;root.append(svg('text',{x:tx,y:ty,'text-anchor':'middle',fill:inferred?'#b66552':'#66877f','font-size':10,'paint-order':'stroke',stroke:'white','stroke-width':4},short(edge.p)));});ids.forEach(id=>{const [x,y]=positions[id];const isPatient=id===patient;const g=svg('g',{class:'graph-node',tabindex:0,role:'button','aria-label':labels[id]});g.append(svg('rect',{x:x-88,y:y-25,width:176,height:50,rx:12,fill:isPatient?'#105464':'#edf6f2',stroke:isPatient?'#105464':'#b9d8cc'}));const label=labels[id]||short(id);let words=label.split(' '),lines=[''];words.forEach(w=>{if((lines[lines.length-1]+' '+w).length>24&&lines[lines.length-1])lines.push(w);else lines[lines.length-1]+=(lines[lines.length-1]?' ':'')+w;});if(lines.length>2)lines=[lines[0],lines.slice(1).join(' ').slice(0,23)+'…'];lines.forEach((line,i)=>g.append(svg('text',{x,y:y+(i-(lines.length-1)/2)*14+4,'text-anchor':'middle','font-size':11,fill:isPatient?'white':'#2a5d54'},line)));g.append(svg('title',{},label+'\n'+id));const select=()=>{$('graph-detail').textContent=label+' · '+id;};g.addEventListener('click',select);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')select();});root.append(g);});table('graph-table',{head:{vars:['labelS','p','labelO']},results:{bindings:data.edges.map(e=>Object.fromEntries(Object.entries(e).map(([k,v])=>[k,{value:v}])) )}});}
$('graph-patient').addEventListener('change',async()=>{try{await drawGraph();}catch(e){$('graph-detail').textContent=e.message;}});
async function init(){try{meta=await api('/api/meta');$('app-version').textContent=meta.counts.version;for(const [id,key]of [['m-meds','medicines'],['m-classes','classes'],['m-patients','patients'],['m-triples','materialized_triples']])$(id).textContent=meta.counts[key];meta.examples.slice(0,6).forEach((q,i)=>{const labels=['Alertes du patient P002','Interactions du patient P004','Effets du Glucophage','Traitements du diabète','Génériques de Clamoxyl','Médicaments avec metformine'];const b=document.createElement('button');b.type='button';b.textContent=labels[i];b.title=q;b.addEventListener('click',()=>{$('question').value=q;$('ask-form').requestSubmit();});$('examples').append(b);});meta.queries.forEach(q=>{const o=document.createElement('option');o.value=q.id;o.textContent=q.title;$('query-select').append(o);});meta.patients.forEach(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=p.label;$('graph-patient').append(o);});$('graph-patient').value='Patient_P002';const health=await api('/api/health');$('backend').textContent=health.backend==='fuseki'?'Fuseki connecté':'Mode local RDFLib';document.querySelector('.status-dot').classList.toggle('online',health.ready);if(!health.ready)throw new Error('Le graphe chargé ne correspond pas au corpus validé. Rechargez le fichier matérialisé.');}catch(e){$('backend').textContent='Connexion à vérifier';$('connection-error').hidden=false;$('connection-error').textContent=e.message;}}


// Ontology explorer: render the actual OWL hierarchy without executing free text.
let ontologyData=null,classMap=new Map(),selectedClass='PenicillineLargeSpectre',expandedClasses=new Set();
function el(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
const normalized=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
function ancestors(id){const result=new Set();function visit(key){for(const p of classMap.get(key)?.parents||[])if(!result.has(p)){result.add(p);visit(p);}}visit(id);return result;}
function classButton(id,text){const b=el('button',text||classMap.get(id)?.label||id,'class-link');b.type='button';b.addEventListener('click',()=>selectClass(id));return b;}
async function loadOntology(){
    ontologyData=await api('/api/ontology');classMap=new Map(ontologyData.classes.map(c=>[c.id,c]));
    const stats=$('ontology-stats');stats.replaceChildren();
    for(const [value,label] of [[ontologyData.counts.classes,'classes nommées'],[ontologyData.counts.max_hierarchy_depth,'niveaux de hiérarchie'],[ontologyData.counts.defined_classes,'classes définies'],[ontologyData.counts.object_properties,'relations objet']]){
        const item=el('div');item.append(el('strong',String(value)),el('span',label));stats.append(item);
    }
    ontologyData.classes.filter(c=>!c.parents.length).forEach(c=>expandedClasses.add(c.id));
    selectClass(selectedClass);
}
function selectClass(id){
    if(!classMap.has(id))return;selectedClass=id;ancestors(id).forEach(p=>expandedClasses.add(p));renderClassTree();renderClassDetail();
}
function renderClassTree(){
    if(!ontologyData)return;
    const filter=normalized($('class-search').value.trim());const matches=new Set();const visible=new Set();
    for(const c of ontologyData.classes)if(!filter||normalized(c.label+' '+c.id).includes(filter)){
        matches.add(c.id);visible.add(c.id);ancestors(c.id).forEach(a=>visible.add(a));
    }
    $('tree-status').textContent=filter?`${matches.size} classe(s) correspondante(s)`:`${ontologyData.classes.length} classes · sélectionnez un libellé`;
    const children=new Map();for(const c of ontologyData.classes)for(const p of c.parents){if(!children.has(p))children.set(p,[]);children.get(p).push(c);}
    const sort=items=>items.sort((a,b)=>a.label.localeCompare(b.label,'fr'));
    function branch(c){
        const li=el('li');const descendants=sort(children.get(c.id)||[]).filter(x=>visible.has(x.id));
        const button=el('button',c.label,'tree-label'+(c.id===selectedClass?' selected':''));button.type='button';button.setAttribute('aria-pressed',String(c.id===selectedClass));button.title=c.id;
        button.append(el('span',String(c.members.length),'member-count'));button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();selectClass(c.id);});
        if(descendants.length){
            const details=el('details');details.className='tree-branch';details.open=!!filter||expandedClasses.has(c.id);const summary=el('summary');summary.append(button);details.append(summary);const list=el('ul');descendants.forEach(d=>list.append(branch(d)));details.append(list);details.addEventListener('toggle',()=>{if(!filter){if(details.open)expandedClasses.add(c.id);else expandedClasses.delete(c.id);}});li.append(details);
        }else li.append(button);
        return li;
    }
    const tree=$('class-tree');tree.replaceChildren();const list=el('ul');sort(ontologyData.classes.filter(c=>!c.parents.length&&visible.has(c.id))).forEach(c=>list.append(branch(c)));tree.append(list);if(!visible.size)tree.append(el('p','Aucune classe ne correspond à cette recherche.','empty'));
}
function sourceLink(url,title='Consulter la source ↗'){
    const a=el('a',title,'source-link');a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;
}
function renderClassDetail(){
    const c=classMap.get(selectedClass),root=$('class-detail');root.replaceChildren();
    root.append(el('span',c.equivalents.length?'CLASSE DÉFINIE':'CLASSE PRIMITIVE','eyebrow'),el('h2',c.label),el('code',c.iri,'iri'),el('p',c.definition,'definition'));
    if(c.parents.length){const p=el('div',undefined,'class-relations');p.append(el('span','Sous-classe de '));c.parents.forEach(id=>p.append(classButton(id)));root.append(p);}
    const children=ontologyData.classes.filter(k=>k.parents.includes(c.id));
    if(children.length){const p=el('div',undefined,'class-relations');p.append(el('span','Sous-classes directes '));children.forEach(k=>p.append(classButton(k.id)));root.append(p);}
    if(c.equivalents.length){root.append(el('h3','Définition équivalente'));c.equivalents.forEach(e=>root.append(el('pre',e,'axiom')));root.append(el('p','Une condition nécessaire et suffisante : HermiT peut déduire l’appartenance à cette classe.','hint'));}
    if(c.constraints.length){root.append(el('h3','Restrictions de cette classe'));c.constraints.forEach(e=>root.append(el('pre',e,'axiom')));}
    root.append(el('h3',`Individus (${c.members.length})`));
    if(!c.members.length)root.append(el('p','Aucun individu dans le corpus actuel. La classe reste disponible pour une extension.','empty'));
    else{
        const list=el('ul',undefined,'member-list');c.members.forEach(member=>{const li=el('li');li.append(el('span',member.label),el('span',member.asserted?'Déclarée':'Inférée',member.asserted?'status-tag':'status-tag derived'));li.title=member.id;list.append(li);});root.append(list);
    }
    if(c.sources.length){root.append(el('h3','Références de classification'));c.sources.forEach(url=>root.append(sourceLink(url,url.includes('atcddd')?'Index ATC · Centre collaborateur OMS ↗':'RCP · Base publique française ↗')));}
}
$('class-search').addEventListener('input',renderClassTree);
$('expand-tree').addEventListener('click',()=>{if(!ontologyData)return;ontologyData.classes.forEach(c=>expandedClasses.add(c.id));renderClassTree();});
$('collapse-tree').addEventListener('click',()=>{expandedClasses.clear();renderClassTree();});

async function loadCatalogue(){if(!meta)meta=await api('/api/meta');renderCatalogue();}
function renderCatalogue(){
    if(!meta)return;const root=$('catalogue-content'),filter=normalized($('medicine-search').value);root.replaceChildren();
    for(const m of meta.medicines.filter(m=>normalized(m.name+' '+m.active+' '+m.cis).includes(filter))){
        const card=el('article',undefined,'medicine-card');card.append(el('span','CIS '+m.cis,'eyebrow'),el('h2',m.name),el('p',m.active+' · '+m.form));const b=el('button','Ouvrir le dossier ↗','subtle');b.addEventListener('click',()=>loadMedicine(m.id));card.append(b);root.append(card);
    }
    if(!root.children.length)root.append(el('p','Aucune spécialité ne correspond à cette recherche.','empty'));
}
let medicineRequest=0;
async function loadMedicine(id){
    const request=++medicineRequest,root=$('medicine-detail');root.hidden=false;root.replaceChildren(el('p','Chargement du dossier…','empty'));
    try{
        const d=await api('/api/medicine/'+encodeURIComponent(id));if(request!==medicineRequest)return;root.replaceChildren();
        const heading=el('div',undefined,'section-title');heading.append(el('h2',d.medicine.name));const close=el('button','Fermer','subtle');close.addEventListener('click',()=>{medicineRequest++;root.hidden=true;});heading.append(close);root.append(heading,el('p','CIS '+d.medicine.cis+' · '+d.route,'hint'));
        const facts=el('dl',undefined,'medicine-facts');for(const [label,value]of [['Substance active',d.active.label],['Masse par unité',d.medicine.strength_mg+' mg de '+d.medicine.strength_substance],['Forme',d.medicine.form],['Statut',d.medicine.classes.includes('SurOrdonnance')?'Sur ordonnance':'Sans ordonnance obligatoire']])facts.append(el('dt',label),el('dd',value));root.append(facts);
        root.append(el('h3','Classification dans l’ontologie'));const tags=el('div',undefined,'class-tags');for(const c of d.classes){const b=el('button',c.label+(c.asserted?'':' · inférée'),c.asserted?'status-tag':'status-tag derived');b.title=c.id;b.addEventListener('click',async()=>{await showView('ontology');$('class-search').value='';selectClass(c.id);});tags.append(b);}root.append(tags);
        root.append(el('h3','Indications sélectionnées'));d.indications.forEach(i=>root.append(el('p',i.label)));
        root.append(el('h3','Contre-indications sélectionnées'));if(!d.contraindications.length)root.append(el('p','Aucune condition encodée dans cette sélection ; le RCP peut en contenir.','hint'));d.contraindications.forEach(c=>{const p=el('p',c.label+' ');p.append(sourceLink(c.source));root.append(p);});
        root.append(el('h3','Effets possibles et fréquence documentée'));const effects=el('ul',undefined,'effect-list');d.effects.forEach(o=>{const li=el('li');li.append(el('strong',o.effect_label),el('span',o.frequency),sourceLink(o.source));effects.append(li);});root.append(effects);
        if(d.reference)root.append(el('p','Référence générique : '+d.reference.name));root.append(el('p',d.medicine.scope,'scope-note'),sourceLink(d.medicine.source,'Fiche complète · Base publique des médicaments ↗'),el('p','Corpus sélectionné le '+d.consulted+'. Les faits de ce dossier sont partiels.','hint'));
        root.scrollIntoView({behavior:'smooth',block:'start'});
    }catch(e){if(request===medicineRequest)root.replaceChildren(el('p',e.message,'empty'));}
}
$('medicine-search').addEventListener('input',renderCatalogue);
function exportCSV(target,filename){
    const result=renderedResults.get(target);if(!result)return;
    const quote=value=>'"'+String(value).replace(/^[=+@-]/,"'$&").replaceAll('"','""')+'"';
    const keys=result.head.vars;const lines=[keys.map(k=>quote((cellLabels[k]||k)+' ['+k+']')).join(';'),...result.results.bindings.map(row=>keys.map(k=>quote(row[k]?.value||'')).join(';'))];
    const url=URL.createObjectURL(new Blob(['\uFEFF'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'}));const a=el('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('export-search').addEventListener('click',()=>exportCSV('result-table','PharmaOnto_recherche.csv'));
$('export-workshop').addEventListener('click',()=>exportCSV('workshop-result','PharmaOnto_'+$('query-select').value+'.csv'));
init();

