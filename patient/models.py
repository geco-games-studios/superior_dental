from django.db import models


class Patient(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(blank=True, null=True)
    gender_choices = [('M', 'Male'), ('F', 'Female')]
    gender = models.CharField(max_length=1, choices=gender_choices, blank=True, null=True)
    nrc = models.CharField(max_length=55,blank=True, null=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    is_patient = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

