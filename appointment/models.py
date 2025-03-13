from django.db import models
from patient.models import Patient
from user_accounts.models import Dentist  # Correctly import the Dentist model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from user_accounts.models import CustomUser 


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE, blank=True, null=True)  # Correctly reference the Dentist model
    date_time = models.DateTimeField()
    status_choices = [('Pending', 'Pending'), ('Scheduled', 'Scheduled'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]
    status = models.CharField(max_length=20, choices=status_choices, default='Pending')
    notes = models.TextField(blank=True, null=True)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_patient_new = models.BooleanField(default=False)

    def __str__(self):
        return f"Appointment for {self.patient} with {self.dentist.user.username} on {self.date_time}"

class Service(models.Model):
    name = models.CharField(max_length=100)  # Required field
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Required field
    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return self.name

class Diagnosis(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, blank=True, null=True)
    diagnosis_text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for {self.appointment.patient} on {self.date}"

class Treatment(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, blank=True, null=True)
    treatment_text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Treatment for {self.appointment.patient} on {self.date}"

class Dentist(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 3}, 
        related_name='appointment_dentist_profile'  # Unique related_name to avoid conflicts
    )
    specialization = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15)
    available_days = models.CharField(max_length=200)

    def __str__(self):
        """
        Returns a string representation of the Dentist object.
        Format: "Dr. {username}"
        """
        if self.user and hasattr(self.user, 'username'):
            return f"Dr. {self.user.username}"
        return "Dr. [No Username]"  # Fallback in case user is None or has no username

    class Meta:
        verbose_name = "Dentist"
        verbose_name_plural = "Dentists"