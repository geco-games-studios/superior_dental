from django.test import TestCase
from django.contrib.auth import get_user_model
from patient.models import Patient
from appointment.models import Service
from payments.models import Invoice, Payment, InvoiceService

class InvoiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.patient = Patient.objects.create(name='John Doe')
        self.service1 = Service.objects.create(name='Cleaning', price=100)
        self.service2 = Service.objects.create(name='Filling', price=200)

    def test_invoice_creation(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            status='issued',
            total_amount=300
        )
        InvoiceService.objects.create(
            invoice=invoice,
            service=self.service1,
            quantity=1,
            price_at_time=100
        )
        InvoiceService.objects.create(
            invoice=invoice,
            service=self.service2,
            quantity=1,
            price_at_time=200
        )
        self.assertEqual(invoice.calculate_total(), 300)

    def test_payment_processing(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            status='issued',
            total_amount=300
        )
        payment = Payment.objects.create(
            patient=self.patient,
            invoice=invoice,
            processed_by=self.user,
            amount=150,
            payment_method='cash'
        )
        self.assertEqual(invoice.get_remaining_balance(), 150)
        self.assertEqual(invoice.status, 'partial')

        payment2 = Payment.objects.create(
            patient=self.patient,
            invoice=invoice,
            processed_by=self.user,
            amount=150,
            payment_method='cash'
        )
        self.assertEqual(invoice.status, 'paid')