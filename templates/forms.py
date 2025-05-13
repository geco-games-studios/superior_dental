from django import forms
from inventory.models import InventoryItem, Supplier, InventoryTransaction, ItemCategory, Supplier

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



class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        exclude = ['last_updated']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'quantity': forms.NumberInput(attrs={'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'min': '0'}),
        }



class TransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['transaction_type', 'quantity', 'reference']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)

        if self.item:
            self.instance.item = self.item

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero")

        if self.instance.transaction_type == 'OUT' and self.item and quantity > self.item.quantity:
            raise forms.ValidationError("Cannot remove more items than available in stock")

        return quantity

class CategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }