from django.shortcuts import render,redirect
from .models import Patient,Appointment
from django.http import  HttpResponseRedirect, JsonResponse
from datetime import date

# Create your views here.

def patients_page(request):
    return render(request, 'patients/patients_page.html')

def patient_login(request):
    return render(request, 'patients/patient_login.html')

def patient_signup(request):
    return render(request, 'patients/patient_signup.html')

def save_patient(request):
    patient = Patient()
    p = Patient.objects.filter(username=request.POST['username'])
    if not p:
        patient.username = request.POST['username']
        patient.name = request.POST['name']
        patient.email = request.POST['email']
        patient.contact = request.POST['contact']
        patient.password = request.POST['password']
        patient.save()
        url = "http://127.0.0.1:8000/login"
        return HttpResponseRedirect(url)
    
    request.session['error_message'] = 'Username already exists!'
    message_to_display = request.session['error_message']
    return render(request, 'patients/patient_signup.html', {'errormsg': message_to_display})

def verify_patient(request):
    try:
        pat = Patient.objects.get(username=request.POST['username'], password=request.POST['password'])
        request.session['patient_id']=pat.id
        request.session['patient_name']=pat.name
        url = "http://127.0.0.1:8000/afterlogin"
    except:
        url = "http://127.0.0.1:8000/login"
    return HttpResponseRedirect(url)

def patient_afterlogin(request):
    patient_name=request.session.get('patient_name')
    print(patient_name)
    return render(request, 'patients/patient_dashboard.html',{'patient_name':patient_name})

def patient_appointments(request):
    patient_id = request.session.get('patient_id')
    if not patient_id:
     return redirect('patient_login')
    
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return redirect('patient_login')

    today = date.today()
    appointments = Appointment.objects.filter(patient_id=patient_id)

    grouped = {
        'upcoming': [],
        'completed': [],
        'cancelled': [],
    }

    for appt in appointments:
        if appt.status.lower() == 'cancelled':
            grouped['cancelled'].append(appt)
        elif appt.appointment_date >= today and appt.status.lower() == 'booked':
            grouped['upcoming'].append(appt)
        else:
            grouped['completed'].append(appt)

    return render(request, 'appointments/patient_appointments.html', {
        'grouped_appointments': grouped
    })

def patient_logout(request):
    request.session.flush()
    return redirect('patients_page')
