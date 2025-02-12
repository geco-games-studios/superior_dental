from django.contrib import admin
from .models import Appointment, Service,Diagnosis,Treatment

admin.site.register(Appointment)
admin.site.register(Service)
admin.site.register(Diagnosis)
admin.site.register(Treatment)
