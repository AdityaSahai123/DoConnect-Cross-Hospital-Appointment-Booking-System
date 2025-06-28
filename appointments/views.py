from django.shortcuts import render, redirect
from django.http import  HttpResponseRedirect, JsonResponse
from django.contrib import messages
from patients.models import  Patient,Appointment
from django.db import connections
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from .global_items import get_gav_mapping
from .global_items import get_gav_mapping_app



def home_page(request):
    return render(request, 'appointments/homePage.html')

def execute_query(query, database):
    try:
        connection = connections[database]
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error executing query on {database}: {e}")
        return []
    print(f"Executing query on {mapping['db']}")

def calculate_similarity(name1, name2):
    """
    Calculates similarity between two strings using Edit Distance.
    Returns True if similarity is more than 90%.
    """
    # Using Edit Distance
    ratio = difflib.SequenceMatcher(None, name1, name2).ratio()
    
    # If the Edit Distance similarity ratio is more than 90%, consider them similar
    return ratio >= 0.8

def get_doctors(request):
    patient_id = request.session.get('patient_id')
    if not patient_id:
     return redirect('patient_login')
    
    GAV_MAPPING = get_gav_mapping()

    specialization = request.POST.get('specialization', None)

    if not specialization:
        return render(request, 'appointments/department_selected.html', {
            "error": "Please select a specialization."
        })

    local_queries = []
    doctors = []
    potential_duplicates = []  

    for source, mapping in GAV_MAPPING["Global_Doctors"].items():
        select_clause = ", ".join([f"{value} AS {key}" for key, value in mapping["columns"].items()])

        spec_col = mapping["columns"].get("specialization")
        where_clause = f"WHERE {spec_col} = '{specialization}'"

        query = f"""
        SELECT {select_clause}
        FROM {mapping['table']}
        {mapping.get('join', '')}
        {where_clause}
        """
        # print(query)
        local_queries.append((query, mapping["db"]))

    for query, database in local_queries:
        result = execute_query(query, database)

        for doctor in result:
            is_duplicate = False

            for other_doctor in doctors:
                if calculate_similarity(doctor[1], other_doctor[1]):  
                    potential_duplicates.append((doctor, other_doctor))
                    is_duplicate = True
                    break

            doctors.append(doctor)

    # Render the result
    return render(request, 'appointments/department_selected.html', {
        'department': specialization,
        'doctors': doctors,
        'potential_duplicates': potential_duplicates  # Send duplicate info to the template
    })

def get_available_slots(request, doctor_id,doctor_name,department):
    # Normalize hospital_name
    patient_id = request.session.get('patient_id')
    if not patient_id:
     return redirect('patient_login')
    
    GAV_MAPPINGApp=get_gav_mapping_app()
    hospital_name = request.GET.get('hospital_name', '').capitalize()
    mapping = GAV_MAPPINGApp["Global_Appointments"].get(hospital_name)

    if not mapping:
        error_message = f"Invalid hospital name: {hospital_name}. Check GAV_MAPPINGApp keys."
        print(error_message)
        messages.error(request, error_message)
        return HttpResponseRedirect("/")

    try:
       
        query = f"""
        SELECT {', '.join([f"{value} AS {key}" for key, value in mapping['available_slots_columns'].items()])}
        FROM {mapping['available_slots_table']}
        WHERE {mapping['available_slots_columns']['doctor_id']} = {doctor_id}
          AND {mapping['available_slots_columns']['is_booked']} = FALSE
        """
        # print(f"Executing Query for {hospital_name}: {query}")

        slots = execute_query(query, mapping['db'])

        if not slots:
            print(f"No slots found for doctor_id {doctor_id} in {hospital_name}.")
            messages.warning(request, f"No available slots found for {hospital_name}.")
            return render(request, 'appointments/available_slots.html', {
                'doctor_id': doctor_id,
                'hospital_name': hospital_name,
                'available_slots': []
            })

        available_slots = [
            dict(zip(mapping['available_slots_columns'].keys(), slot))
            for slot in slots
        ]
        
        return render(request, 'appointments/available_slots.html', {
            'doctor_id': doctor_id,
            'doctor_name':doctor_name,
            'department':department,
            'hospital_name': hospital_name,
            'available_slots': available_slots
        })
    except Exception as e:
        error_message = f"Error executing query on {hospital_name}: {e}"
        print(error_message)
        messages.error(request, error_message)
        return HttpResponseRedirect("/get_doctors/")

def execute_update_query(query, database):
    """
    Executes an update query on the given database and returns the number of rows affected.
    """
    try:
        connection = connections[database]
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows_affected = cursor.rowcount  # Get the number of rows affected
            connection.commit()  # Ensure the transaction is committed
            return rows_affected
    except Exception as e:
        print(f"Error executing update query on {database}: {e}")
        raise

# def book_appointment(request):
#     if request.method == "POST":
#         doctor_id = request.POST.get('doctor_id')
#         patient_id = request.session['patient_id']
#         appointment_date = request.POST.get('appointment_date')
#         appointment_time = request.POST.get('appointment_time')
#         hospital_name = request.POST.get('hospital_name').strip()  # Clean up the input

#         # Validate the appointment_time format
#         try:
#             appointment_time = datetime.strptime(appointment_time, '%H:%M:%S').time()
#         except ValueError:
#             return JsonResponse({'status': 'error', 'message': 'Invalid time format. Use HH:MM:SS.'}, status=400)

#         # Look up hospital details in the mapping
#         mapping = GAV_MAPPINGApp["Global_Appointments"].get(hospital_name)
#         if not mapping:
#             return JsonResponse({'status': 'error', 'message': 'Invalid hospital name.'}, status=400)

#         try:
#             # Update the slot to mark it as booked
#             update_slots_query = f"""
#             UPDATE {mapping['available_slots_table']}
#             SET is_booked = TRUE
#             WHERE doctor_id = {doctor_id}
#               AND slot_date = '{appointment_date}'
#               AND slot_time = '{appointment_time}'
#               AND is_booked = FALSE;
#             """
            
#             # Execute the query
#             rows_affected = execute_update_query(update_slots_query, mapping['db'])

#             # Check if the update was successful
#             if rows_affected == 0:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Slot booking failed. The slot may already be booked or does not exist.'
#                 }, status=400)

#             # Redirect to confirmation page
#             return HttpResponseRedirect("/appointment_confirmation/")

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)

#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

def book_appointment(request):
    patient_id = request.session.get('patient_id')
    if not patient_id:
     return redirect('patient_login')
    
    GAV_MAPPINGApp=get_gav_mapping_app()
    if request.method == "POST":
        doctor_id = request.POST.get('doctor_id')
        doctor_name = request.POST.get('doctor_name')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        department = request.POST.get('department', 'Unknown')
        hospital_name = request.POST.get('hospital_name').strip()

        patient_id = request.session.get('patient_id')
        if not patient_id:
            return JsonResponse({'status': 'error', 'message': 'User session expired. Please log in again.'}, status=401)

        # Validate time
        try:
            appointment_time = datetime.strptime(appointment_time, '%H:%M:%S').time()
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid time format. Use HH:MM:SS.'}, status=400)

        mapping = GAV_MAPPINGApp["Global_Appointments"].get(hospital_name)
        if not mapping:
            return JsonResponse({'status': 'error', 'message': 'Invalid hospital name.'}, status=400)

        try:
            # Update external DB
            slot_cols = mapping['available_slots_columns']

            update_slots_query = f"""
                UPDATE {mapping['available_slots_table']}
                SET {slot_cols['is_booked']} = TRUE
                WHERE {slot_cols['doctor_id']} = {doctor_id}
                AND {slot_cols['slot_date']} = '{appointment_date}'
                AND {slot_cols['slot_time']} = '{appointment_time}'
                AND {slot_cols['is_booked']} = FALSE;
            """
            # print(update_slots_query)

            rows_affected = execute_update_query(update_slots_query, mapping['db'])

            if rows_affected == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Slot booking failed. The slot may already be booked or does not exist.'
                }, status=400)

            patient = Patient.objects.get(id=patient_id)
            Appointment.objects.create(
                patient=patient,
                hospital_name=hospital_name,
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                department=department,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='Booked'
            )

            return HttpResponseRedirect("/appointment_confirmation/")
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

def cancel_appointment(request):
    patient_id = request.session.get('patient_id')
    if not patient_id:
     return redirect('patient_login')
    
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        appointment = Appointment.objects.filter(id=appointment_id).first()
        if not appointment:
            return JsonResponse({'status': 'error', 'message': 'Appointment not found'})

        # Update internal
        appointment.status = 'cancelled'
        appointment.save()

        # Update external
        GAV = get_gav_mapping_app()
        mapping = GAV['Global_Appointments'].get(appointment.hospital_name)
        if mapping:
            slot_cols = mapping['available_slots_columns']
            update_sql = f"""
                UPDATE {mapping['available_slots_table']}
                SET {slot_cols['is_booked']} = FALSE
                WHERE {slot_cols['doctor_id']} = {appointment.doctor_id}
                AND {slot_cols['slot_date']} = '{appointment.appointment_date}'
                AND {slot_cols['slot_time']} = '{appointment.appointment_time}'
            """
            # print(update_sql)
            execute_update_query(update_sql, mapping['db'])

        return redirect('patient_appointments')
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def appointment_confirmation(request):
    """
    Show appointment confirmation message after booking.
    """
    patient_name=request.session.get('patient_name')
    return render(request, 'appointments/appointment_confirmation.html',{'patient_name':patient_name})

def patient_afterlogin(request):
    """
    After patient logs in, show their appointments or a welcome page.
    """

    return render(request, 'appointments/patient_afterlogin.html')

def doctors_page(request):
    patient_id = request.session.get('patient_id')
    if not patient_id:
     return redirect('patient_login')
    
    return render(request, 'appointments/doctors_page.html')

def select_departments(request):
     patient_id = request.session.get('patient_id')
     if not patient_id:
      return redirect('patient_login')
    
     return render(request, 'appointments/select_departments.html')



