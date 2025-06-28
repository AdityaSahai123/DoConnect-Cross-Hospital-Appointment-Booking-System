from django.db import models

class Patient(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255)
    contact = models.CharField(max_length=10)
    name = models.CharField(max_length=100, default='')
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    hospital_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    doctor_name = models.CharField(max_length=100, null=True, blank=True)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=50, default='Booked')

    def __str__(self):
        return f"{self.patient.name} - {self.hospital_name} ({self.department})"

