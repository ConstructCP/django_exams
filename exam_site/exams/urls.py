from django.urls import path
from . import views


app_name = 'exams'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('<exam_id>/', views.ExamView.as_view(), name='exam'),
    path('<exam_id>/results', views.exam_result, name='exam_results'),
]
