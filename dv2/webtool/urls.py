from django.urls import include, path
from rest_framework import routers
from . import views


router = routers.DefaultRouter()
router.register(r'questions', views.QuestionViewSet)


urlpatterns = [
    path('api/v1.0/', include(router.urls)),
    path('', views.index, name='index'),
]
