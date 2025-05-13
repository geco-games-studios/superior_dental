from django import forms
from .models import InventoryItem, Supplier, InventoryTransaction

class ItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'

class TransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['transaction_type', 'quantity', 'reference']


