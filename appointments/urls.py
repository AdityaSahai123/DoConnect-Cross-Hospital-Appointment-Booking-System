from django.urls import path
from . import views

urlpatterns = [
  
    path('select_departments/',views.select_departments,name='select_departments'),
    path('doctors/', views.doctors_page, name='doctors_page'),
    
    path('get_doctors/', views.get_doctors, name='get_doctors'),  
    # urls.py
    path(
        'get_available_slots/<int:doctor_id>/<str:doctor_name>/<str:department>/',
        views.get_available_slots,
        name='get_available_slots'
    ),
    path('book_appointment/', views.book_appointment, name='book_appointment'), 
    path('cancel_appointment/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment_confirmation/', views.appointment_confirmation, name='appointment_confirmation'),

    
]
