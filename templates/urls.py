from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('app/', views.app_login, name='app'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard', views.Dashboard, name='dashboard'),
    path('patients', views.PatientsPage, name='patients'),
    path('create-patient', views.CreatePatient, name='create-patient'),
    path('appointments', views.AppointmentsPage, name='appointments'),
    path('create_user/', views.create_user, name='create_user'),
    path('register/dentist/', views.create_user, name='create_user'),
    path('register/staff/', views.create_user, name='create_user'),
    path('dentists', views.DentistsPage, name='dentists'),
    path('create_admin/', views.create_user, name='create_user'),
    path('create_appointment/', views.create_appointment, name='create_appointment'),
    path('walkin_appointment/', views.walk_in_appointment, name='walkin_appointment'),
    path('clear_appointment_created_flag/', views.clear_appointment_created_flag, name='clear_appointment_created_flag'),
    path('patient_details/<int:id>', views.patient_details, name='patient_details'),
    path('assign_dentist/', views.assign_dentist, name='assign_dentist'),
    path('treatment_diagnosis', views.treatment_diagnosis, name='treatment_diagnosis'),
    path('scheduled_appointment', views.scheduled_appointment_view, name='scheduled_appointment'),
    
]