from django.urls import path
from . import views
urlpatterns=[path('',views.index),path('static/<str:name>',views.asset),path('api/health',views.status),path('api/meta',views.metadata),path('api/query/<str:key>',views.predefined),path('api/ask',views.ask),path('api/graph',views.graph),path('api/ontology',views.ontology),path('api/medicine/<str:identifier>',views.medicine),path('download/<str:kind>',views.download)]
