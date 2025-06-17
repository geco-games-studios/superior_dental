from django.conf import settings
from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from django.utils import timezone
import uuid
from patient.models import Patient
from appointment.models import Appointment, Service


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid')
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    services = models.ManyToManyField(Service, through='InvoiceService')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_payments(self):
        return self.payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def calculate_total(self):
        return self.invoiceservice_set.aggregate(
            total=Sum(F('price_at_time') * F('quantity'))
        )['total'] or Decimal('0.00')

    def update_total_amount(self):
        self.total_amount = self.calculate_total()
        self.save(update_fields=['total_amount'])

    def get_remaining_balance(self):
        total_payments = Payment.objects.filter(invoice=self, status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        return max(Decimal('0.00'), self.total_amount - total_payments)



class InvoiceService(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure price_at_time is always populated
        if not self.price_at_time:
            if self.service.price is None:
                raise ValueError("Service price cannot be None.")
            self.price_at_time = self.service.price

        super().save(*args, **kwargs)
        self.invoice.update_total_amount()

    def __str__(self):
        return f"{self.quantity} x {self.service.name}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mobile', 'Mobile Payment'),
        ('bank', 'Bank Transfer')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('ongoing', 'Ongoing')
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_invoice_status()

    def update_invoice_status(self):
        total_paid = Payment.objects.filter(
            invoice=self.invoice, 
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        if total_paid >= self.invoice.total_amount:
            self.invoice.status = 'paid'
        elif total_paid > 0:
            self.invoice.status = 'partial'
        else:
            self.invoice.status = 'issued'

        self.invoice.save(update_fields=['status'])

    def __str__(self):
        return f"Payment of K{self.amount} by {self.patient}"


class Receipt(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    items = models.ManyToManyField('inventory.InventoryItem', through='ReceiptItem')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,  # Allow NULL values
        blank=True,  # Allow blank values in forms
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price of the item at the time of receipt creation."
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RECEIPT-{uuid.uuid4().hex[:8]}"
        
        if self.payment:
            self.total_amount = self.payment.amount
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt: {self.receipt_number}"


class ReceiptItem(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)
    item = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price of the item at the time of receipt creation."
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item.name}"


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    services = models.ManyToManyField(Service, through='QuotationService')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    valid_until = models.DateField(null=True, blank=True)  # Optional field

    def calculate_total(self):
        return self.quotationservice_set.aggregate(
            total=Sum(F('price_at_time') * F('quantity'))
        )['total'] or Decimal('0.00')

    def update_total_amount(self):
        self.total_amount = self.calculate_total()
        self.save(update_fields=['total_amount'])

    def __str__(self):
        return f"Quotation for {self.patient}"


class QuotationService(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.price_at_time:
            self.price_at_time = self.service.price
        super().save(*args, **kwargs)
        self.quotation.update_total_amount()

    def __str__(self):
        return f"{self.quantity} x {self.service.name}"