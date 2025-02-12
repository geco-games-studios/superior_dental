from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# Define the CustomUserManager class
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

# Define the CustomUser model
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        (1, 'Admin'),
        (2, 'Staff'),
        (3, 'Dentist'),
    ]
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES)

    # Use the custom manager
    objects = CustomUserManager()

    def __str__(self):
        return self.username
    


class Dentist(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 3}, 
        related_name='user_accounts_dentist_profile'  # Unique related_name
    )
    specialization = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15)
    available_days = models.CharField(max_length=200)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"
    

class Staff(models.Model):
    user = models.OneToOneField('user_accounts.CustomUser', on_delete=models.CASCADE, limit_choices_to={'user_type': 2}, related_name='staff_profile')
    role = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.role}"

