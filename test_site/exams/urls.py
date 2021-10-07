from django.urls import path
from . import views


app_name = 'exams'
urlpatterns = [
    path('', views.index, name='index'),
    path('<exam_name>/', views.exam, name='exam'),
    path('<exam_name>/results', views.exam_result, name='exam_results')
]
