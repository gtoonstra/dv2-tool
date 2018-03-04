from django.urls import include, path
from rest_framework import routers
from . import views


router = routers.DefaultRouter()
router.register(r'schemas', views.SchemaViewSet)
router.register(r'tables', views.TableViewSet)
router.register(r'columns', views.ColumnViewSet)

app_name = 'webtool'

urlpatterns = [
    path('api/v1.0/', include(router.urls)),
    path('api/v1.0/connect', views.connect),
    path('', views.index, name='index'),
    path('parse', views.parse, name='parse'),
    path('generate', views.generate, name='generate'),
]
