from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from patient.models import Patient
from appointment.models import Appointment, Service, Treatment, Diagnosis
from django.contrib import messages
from user_accounts.forms import CustomUserCreationForm, DentistForm, StaffForm
from user_accounts.models import CustomUser, Dentist, Staff
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from user_accounts.forms import CustomUserCreationForm
from django.contrib.auth import logout




def app_login(request):
    return render(request, 'login.html')

def is_admin(user):
    return user.user_type == 1

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    users = CustomUser.objects.all()
    return render(request, 'admin_dashboard.html', {'users': users})



class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        # Set default user_type for superuser (e.g., 1 for Admin)
        extra_fields.setdefault('user_type', 1)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)
    



def create_admin(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 1  # Set the user type to Admin (assuming 1 corresponds to Admin)
            user.save()
            messages.success(request, "Admin account created successfully!")
            return redirect('admin_dashboard')  # Redirect to the admin dashboard or another URL
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_admin.html', {'form': form})

def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')  # Redirect to the login page or another URL
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_user.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember')  # Get remember me value
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry
            if not remember_me:
                # Session will expire when browser closes
                request.session.set_expiry(0)
            
            # Redirect based on user type
            if user.user_type == 1:
                return redirect('dashboard')
            elif user.user_type == 2:
                return redirect('dashboard')
            elif user.user_type == 3:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    
    # If GET request or failed login, show login page
    return render(request, 'login.html')  # Make sure this matches your template name




def logout_view(request):
    logout(request)  # Logs the user out
    return redirect('login')


def DentistsPage(request):
    dentists = Dentist.objects.all()
    return render(request, 'dentists.html', {'dentists': dentists})

@login_required
def Dashboard(request):
    return render(request, 'dashboard.html')
@login_required
def PatientsPage(request):
    patients = Patient.objects.all()
    return render(request, 'patients.html', {'patients': patients})

@login_required
def CreatePatient(request):
    if request.method == 'POST':
       first_name = request.POST.get('first-name')
       last_name = request.POST.get('last-name')
       date_of_birth = request.POST.get('dob')
       gender = request.POST.get('gender')
       nrc = request.POST.get('nrc')
       contact_number = request.POST.get('phone')
       email = request.POST.get('email')
       address = request.POST.get('address')
       medical_history = request.POST.get('medical_history', '')

    Patient.objects.create(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        nrc=nrc,
        contact_number=contact_number,
        email=email,
        address=address,
        medical_history=medical_history,
        is_patient=True
    )

    messages.success(request, 'Patient created successfully!')

    return render(request, 'patients.html')

def AppointmentsPage(request):
    appointments = Appointment.objects.filter(status='Pending')
    dentists = Dentist.objects.filter(user__user_type=3)
    print(dentists)  # Debugging: Check if dentists are fetched
    return render(request, 'appointments.html', {'appointments': appointments, 'dentists': dentists})

def index(request):
    # Retrieve only services with valid name and price
    services = Service.objects.filter(name__isnull=False, price__isnull=False)
    
    # Debugging: Print raw SQL query and retrieved services
    print("[DEBUG] Raw Query:", services.query)
    print("[DEBUG] Retrieved Services:", [(s.id, s.name, s.price) for s in services])

    if not services.exists():
        print("[WARNING] No services found in the database.")
        messages.warning(request, "No services available. Please contact the administrator.")

    return render(request, 'index.html', {'services': services})


@csrf_exempt
def clear_appointment_created_flag(request):
    if request.method == 'POST':
        request.session.pop('appointment_created', None)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)



@csrf_protect
def create_appointment(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            appoint_date = request.POST.get('appoint_date')
            appoint_time = request.POST.get('appoint_time')
            service_id = request.POST.get('service')
            notes = request.POST.get('notes')

            # Handle cases where full_name does not contain a space
            if ' ' in full_name:
                first_name, last_name = full_name.rsplit(' ', 1)
            else:
                messages.error(request, "Full name must include both first and last names.")
                return redirect('index')

            # Check if the service exists
            try:
                service = Service.objects.get(id=service_id)
            except ObjectDoesNotExist:
                messages.error(request, "Invalid service selected.")
                return redirect('index')

            # Ensure a dentist is available
            dentist = Dentist.objects.first()
            if not dentist:
                messages.error(request, "No dentists available to assign appointments.")
                return redirect('index')

            # Parse and validate date and time
            try:
                date_time_str = f"{appoint_date} {appoint_time}"
                naive_date_time = timezone.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
                aware_date_time = timezone.make_aware(naive_date_time, timezone.get_default_timezone())
            except ValueError:
                messages.error(request, "Invalid date or time format. Please use YYYY-MM-DD HH:MM.")
                return redirect('index')

            # Create or retrieve the patient
            patient, created = Patient.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                defaults={'phone': phone}
            )

            # Create the appointment
            appointment = Appointment.objects.create(
                patient=patient,
                dentist=dentist,
                date_time=aware_date_time,
                service=service,
                notes=notes
            )

            # Notify via Channels
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "appointment_notifications",
                    {
                        "type": "send_notification",
                        "message": f"New appointment: {appointment.patient.first_name} {appointment.patient.last_name}, Service: {appointment.service.name}, Date: {appointment.date_time.strftime('%Y-%m-%d %H:%M')}"
                    }
                )

            # Set session flag and redirect
            request.session['appointment_created'] = True
            messages.success(request, "Appointment created successfully!")
            return redirect('index')

        except Exception as e:
            # Catch unexpected errors and log them
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('index')

    # Handle GET requests
    return render(request, 'index.html')
@login_required
@csrf_protect
def walk_in_appointment(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        appoint_date = request.POST.get('appoint_date')
        appoint_time = request.POST.get('appoint_time')
        service_id = request.POST.get('service')
        notes = request.POST.get('notes')

        first_name, last_name = full_name.split(' ', 1)

        patient, created = Patient.objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            defaults={'phone': phone}
        )

        service = Service.objects.get(id=service_id)

        dentist = Dentist.objects.first()

        date_time_str = f"{appoint_date} {appoint_time}"
        naive_date_time = timezone.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
        aware_date_time = timezone.make_aware(naive_date_time, timezone.get_default_timezone())

        appointment = Appointment.objects.create(
            patient=patient,
            dentist=dentist,
            date_time=aware_date_time,
            service=service,
            notes=notes
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "appointment_notifications",
            {
                "type": "send_notification",
                "message": f"New appointment: {appointment.patient.first_name} {appointment.patient.last_name}, Service: {appointment.service.name}, Date: {appointment.date_time.strftime('%Y-%m-%d %H:%M')}"
            }
        )

        request.session['appointment_created'] = True

        return redirect('appointments')

    return render(request, 'appointments.html')

def patient_details(request, id):
    patient = get_object_or_404(Patient, id=id)
    appointments = Appointment.objects.filter(patient=patient)
    treatments = Treatment.objects.filter(appointment__in=appointments)
    diagnoses = Diagnosis.objects.filter(appointment__in=appointments)
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'treatments': treatments,
        'diagnoses': diagnoses,
    }
    
    return render(request, 'patient_details.html', context)

@login_required
def assign_dentist(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointmentId')
        dentist_id = request.POST.get('dentist')
        print('Function called')
        
        if not appointment_id or not dentist_id:
            return JsonResponse({'success': False, 'message': 'Missing appointment or dentist ID.'})
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        dentist = get_object_or_404(Dentist, id=dentist_id)
        
        appointment.dentist = dentist
        appointment.status = 'Scheduled'  # Correctly update the status field
        appointment.save()
        print('After saving appointment:', appointment.status)  # Debugging: Check if the status is updated
        
        # send_mail(
        #     'New Appointment Assigned',
        #     f'Dear {dentist.user.first_name},\n\nYou have been assigned a new appointment with {appointment.patient.first_name} {appointment.patient.last_name} on {appointment.date_time}.\n\nBest Regards,\nSuperior Dental Solutions',
        #     'clinic@example.com',
        #     [dentist.user.email],  # Use dentist.user.email
        #     fail_silently=False,
        # )
        
        return JsonResponse({'success': True, 'message': 'Dentist assigned and notification sent.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
@login_required
def scheduled_appointment_view(request):
    scheduled_appointments = Appointment.objects.filter(status='Scheduled')
    return render(request, 'schuled_appointment.html', {'scheduled_appointments': scheduled_appointments})

@login_required
def treatment_diagnosis(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointmentId')
        service_id = request.POST.get('service')
        treatment_text = request.POST.get('treatment_text')
        diagnosis_text = request.POST.get('diagnosis_text')
        
        if not appointment_id or not service_id or not treatment_text or not diagnosis_text:
            return JsonResponse({'success': False, 'message': 'Missing required fields.'})
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        service = get_object_or_404(Service, id=service_id)
        
        treatment = Treatment.objects.create(
            appointment=appointment,
            service=service,
            treatment_text=treatment_text
        )
        
        diagnosis = Diagnosis.objects.create(
            appointment=appointment,
            service=service,
            diagnosis_text=diagnosis_text
        )
        
        return JsonResponse({'success': True, 'message': 'Treatment and diagnosis saved successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
