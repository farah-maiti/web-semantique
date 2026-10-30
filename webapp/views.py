import json
from django.http import JsonResponse,FileResponse,Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET,require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from scripts.build_ontology import ROOT
from .queries import QUERIES,query
from .semantic import execute,rows,health,BackendUnavailable,entity_graph
from .nlp import translate,UnsupportedQuestion,EXAMPLES
from .explorer import ontology_snapshot,medicine_detail

@ensure_csrf_cookie
@require_GET
def index(request):return render(request,'index.html')

@require_GET
def asset(request,name):
    allowed={'app.js':'application/javascript','style.css':'text/css'}
    if name not in allowed:raise Http404
    return FileResponse(open(ROOT/'webapp/static'/name,'rb'),content_type=allowed[name])

@require_GET
def status(request):
    try:return JsonResponse(health())
    except BackendUnavailable as e:return JsonResponse({'ready':False,'error':str(e)},status=503)

@require_GET
def metadata(request):
    corpus=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf-8'))
    return JsonResponse({'counts':json.loads((ROOT/'validation/counts.json').read_text()),'examples':EXAMPLES,'queries':[{'id':k,'title':v[0]} for k,v in QUERIES.items()],'patients':[{'id':p['id'],'label':p['label']} for p in corpus['patients']],'medicines':[{'id':m['id'],'name':m['name'],'active':m['active'],'form':m['form'],'cis':m['cis']} for m in corpus['medicines']],'consulted':corpus['consulted'],'classification_reviewed':corpus['classification_reviewed']})

@require_GET
def predefined(request,key):
    if key not in QUERIES:return JsonResponse({'error':'Requête inconnue'},status=404)
    sparql=query(key)
    try:return JsonResponse({'title':QUERIES[key][0],'sparql':sparql,'result':execute(sparql)})
    except BackendUnavailable as e:return JsonResponse({'error':str(e)},status=503)

@require_POST
def ask(request):
    try:
        payload=json.loads(request.body)
        if not isinstance(payload,dict):raise UnsupportedQuestion('Objet JSON attendu.')
        translated=translate(payload.get('question'))
        translated['result']=execute(translated['sparql'])
        translated['message']='Résultats du corpus partiel. Une absence de résultat ne prouve pas une absence de risque.'
        return JsonResponse(translated)
    except (ValueError,TypeError,UnicodeDecodeError) as e:return JsonResponse({'error':str(e),'examples':EXAMPLES},status=400)
    except BackendUnavailable as e:return JsonResponse({'error':str(e)},status=503)

@require_GET
def graph(request):
    try:return JsonResponse({'edges':entity_graph(request.GET.get('patient','Patient_P002'))})
    except ValueError as e:return JsonResponse({'error':str(e)},status=400)
    except BackendUnavailable as e:return JsonResponse({'error':str(e)},status=503)

@require_GET
def ontology(request):
    try:return JsonResponse(ontology_snapshot())
    except BackendUnavailable as e:return JsonResponse({'error':str(e)},status=503)

@require_GET
def medicine(request,identifier):
    try:return JsonResponse(medicine_detail(identifier))
    except ValueError as e:return JsonResponse({'error':str(e)},status=404)
    except BackendUnavailable as e:return JsonResponse({'error':str(e)},status=503)

@require_GET
def download(request,kind):
    files={'owl':'pharmaonto.owl','swrl':'pharmaonto-swrl.owl','turtle':'pharmaonto.ttl'}
    if kind not in files:raise Http404
    name=files[kind]
    return FileResponse(open(ROOT/'ontology'/name,'rb'),as_attachment=True,filename=name)
