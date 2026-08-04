from django import forms
from product.models import Product
from django.contrib.auth.forms import UserCreationForm
from delivery.models import CustomUser
from .models import DeliveryAssignment
from product.models import Order  # ou le bon chemin vers ton modèle Order

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('seller', 'created_at')  # ✅ Le champ seller sera défini automatiquement
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'main_category': forms.Select(attrs={'class': 'form-select'}),
            'target_audience': forms.Select(attrs={'class': 'form-select'}),
        }

class LivreurCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_livreur = True
        user.is_active = True  # tu peux mettre False si tu veux une validation manuelle
        if commit:
            user.save()
        return user

class DeliveryAssignmentForm(forms.ModelForm):
    class Meta:
        model = DeliveryAssignment
        fields = ['delivery_person']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery_person'].queryset = CustomUser.objects.filter(is_livreur=True, is_active=True)
