from django.contrib import admin
from .models import Invoice, InvoiceService, Payment, Quotation

admin.site.register(Invoice)
admin.site.register(InvoiceService)
admin.site.register(Payment)
admin.site.register(Quotation)

# Register your models here.
