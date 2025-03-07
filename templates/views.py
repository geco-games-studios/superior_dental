from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from patient.models import Patient
from appointment.models import Appointment, Service, Treatment, Diagnosis
from django.contrib import messages
from user_accounts.forms import CustomUserCreationForm, DentistForm, StaffForm
from user_accounts.models import CustomUser, Dentist, Staff
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, Http404
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
    logined_user = request.user.username
    total_appointments = Appointment.objects.all().count()
    total_patients = Patient.objects.all().count()
    scheduled_appointments = Appointment.objects.filter(status='Scheduled')
    pending_appointments = Appointment.objects.filter(status='Pending')
    completed_appointments = Appointment.objects.filter(status='Completed')
    cancelled_appointments = Appointment.objects.filter(status='Cancelled')
    return render(request, 'dashboard.html', {'scheduled_appointments': scheduled_appointments, 'pending_appointments': pending_appointments, 'completed_appointments': completed_appointments, 'cancelled_appointments': cancelled_appointments, 'logined_user': logined_user, 'total_appointments': total_appointments, 'total_patients': total_patients, 'total_appointments': total_appointments})
    
@login_required
def PatientsPage(request):
    patients = Patient.objects.filter(is_patient=True).order_by('-id')
    return render(request, 'patients.html', {'patients': patients})

@login_required
def CreatePatient(request):
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first-name', '').strip()
        last_name = request.POST.get('last-name', '').strip()
        date_of_birth = request.POST.get('dob', '').strip()
        gender = request.POST.get('gender', '').strip()
        nrc = request.POST.get('nrc', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        medical_history = request.POST.get('medical_history', '').strip()

        # Validate required fields
        if not all([first_name, last_name, date_of_birth, gender, nrc, phone]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'create_patient.html')

        # Create the patient
        try:
            Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender,
                nrc=nrc,
                phone=phone,
                email=email,
                address=address,
                medical_history=medical_history,
                is_patient=True
            )
            messages.success(request, 'Patient created successfully!')
            return redirect('patients')  # Redirect to the patients list page
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'create_patient.html')

    # Render the form for GET requests
    return render(request, 'create_patient.html')



def AppointmentsPage(request):
    # Retrieve pending appointments
    appointments = Appointment.objects.filter(status='Pending')
    
    # Retrieve dentists with user_type=3
    dentists = Dentist.objects.filter(user__user_type=3)
    
    # Retrieve services with valid name and price
    services = Service.objects.filter(name__isnull=False, price__isnull=False)
    
    # Pass all data to the template
    return render(
        request,
        'appointments.html',
        {
            'appointments': appointments,  # Pending appointments
            'dentists': dentists,         # List of dentists
            'services': services          # Services with valid name and price
        }
    )


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


@csrf_protect
def walk_in_appointment(request):
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
            return redirect('appointments')

        except Exception as e:
            # Catch unexpected errors and log them
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('appointments')

    # Handle GET requests
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

        if not appointment_id or not dentist_id:
            return JsonResponse({'success': False, 'message': 'Missing appointment or dentist ID.'})

        try:
            appointment = Appointment.objects.get(id=appointment_id)
            dentist = Dentist.objects.get(id=dentist_id)
        except (Appointment.DoesNotExist, Dentist.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Invalid appointment or dentist ID.'})

        # Assign dentist and set status to 'Scheduled'
        appointment.dentist = dentist
        appointment.status = 'Scheduled'

        try:
            appointment.save()  # Save the changes to the database
        except Exception as e:
            print(f'Error saving appointment: {e}')
            return JsonResponse({'success': False, 'message': f'Error saving appointment: {e}'})

        return JsonResponse({'success': True, 'message': 'Dentist assigned successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    

@login_required
def scheduled_appointment_view(request):
    scheduled_appointments = Appointment.objects.filter(status='Scheduled')
    return render(request, 'schuled_appointment.html', {'scheduled_appointments': scheduled_appointments})
from django.shortcuts import get_object_or_404, render, Http404

def treatment_request(request, patient_id):
    try:
        # Fetch the patient object or raise 404 if not found
        patient = get_object_or_404(Patient, id=patient_id)
    except Exception as e:
        print(f"Error fetching patient: {e}")
        raise Http404("Patient not found")

    # Pass the patient object to the template for display
    context = {
        'patient': patient,
    }
    return render(request, 'treatment_request.html', context)  # Pass `request` as the first argument

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

def update_patient_request(request, patient_id):
    try:
        # Fetch the patient object or raise 404 if not found
        patient = get_object_or_404(Patient, id=patient_id)
    except Exception as e:
        print(f"Error fetching patient: {e}")
        messages.error(request, "Failed to fetch the patient. Please try again.")
        return redirect('patients')  # Redirect to the patients list page

    try:
        # Fetch services object or raise 404 if not found
        services = Service.objects.filter(name__isnull=False, price__isnull=False).order_by('name')
        print(f"List of services: {[(s.id, s.name, s.price) for s in services]}")  # Debug statement
    except Exception as e:
        print(f"Error fetching services: {e}")
        services = []  # Fallback to an empty list if an error occurs

    if not services:
        print("[WARNING] No services found matching the filter criteria.")
        messages.warning(request, "No services available. Please contact the administrator.")

    # Pass the patient object and services to the template for display
    context = {
        'patient': patient,
        'services': services,
    }
    return render(request, 'update_patient.html', context)


def update_patient(request):
    if request.method == 'POST':
        # Retrieve form data from the POST request
        patient_id = request.POST.get('patient_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        nrc = request.POST.get('nrc')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('dob')
        address = request.POST.get('address')

        try:
            # Attempt to fetch the patient by ID
            patient = get_object_or_404(Patient, id=patient_id)

            # Update patient fields
            patient.first_name = first_name
            patient.last_name = last_name
            patient.date_of_birth = date_of_birth
            patient.email = email
            patient.phone = phone
            patient.nrc = nrc
            patient.gender = gender
            patient.address = address
            patient.is_patient = True  # Assuming this field exists in your model

            # Save the updated patient
            patient.save()

            # Add success message
            messages.success(request, 'Patient updated successfully!')
        except Patient.DoesNotExist:
            # Handle the case where the patient does not exist
            messages.error(request, 'Failed to update the patient. The patient does not exist.')

        # Redirect to the patients page
        return redirect('patients')

    else:
        # If the request method is not POST, show an error message
        messages.error(request, 'Failed to update the patient. Make sure all required fields are filled.')
        return redirect('patients')

def complete_appointment(request, appointment_id):
    try:
        # Attempt to fetch the appointment by ID
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Fetch the associated patient
        patient = appointment.patient
        print(f"Received appointment_id: {appointment_id}")

        # Check if the patient's KYC is complete
        if patient.is_patient:  # Assuming `is_patient` indicates incomplete KYC
            messages.error(request, 'Patient KYC is not complete. Please complete the KYC first.')
            return redirect('dashboard', {'messages': messages})

        # Mark the appointment as completed
        appointment.status = 'Completed'
        appointment.save()

        # Add success message
        messages.success(request, 'Appointment marked as completed.')

    except Appointment.DoesNotExist:
        # Handle the case where the appointment does not exist
        messages.error(request, 'Appointment not found.')

    # Redirect to the dashboard
    return redirect('dashboard')