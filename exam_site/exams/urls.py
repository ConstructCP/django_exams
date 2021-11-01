from django.urls import path
from . import views


app_name = 'exams'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('healthcheck/', views.health_check_view, name='healthcheck'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('<exam_id>/setup/', views.ExamSetupView.as_view(), name='exam_setup'),
    path('<exam_id>/take/', views.ExamTakeView.as_view(), name='exam_take'),
    path('<exam_id>/save/', views.ExamSave.as_view(), name='exam_save'),
    path('<exam_id>/<str:exam_record_datetime>/', views.ExamResultView.as_view(), name='exam_results'),
    # path('<exam_id>/results', views.exam_result, name='exam_results'),
]
