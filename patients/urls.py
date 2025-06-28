from django.urls import path
from . import views

urlpatterns = [

    path('patient_page/', views.patients_page, name='patients_page'),
    path('login/', views.patient_login, name='patient_login'),
    path('signup/', views.patient_signup, name='patient_signup'),
    path('save_patient/', views.save_patient, name='save_patient'),
    path('verify_patient/', views.verify_patient, name='verify_patient'),
    path('afterlogin/', views.patient_afterlogin, name='patient_afterlogin'),
    path('patient_appointments/',views.patient_appointments,name='patient_appointments'),
    path('patient_logout/', views.patient_logout, name='patient_logout'),

]
