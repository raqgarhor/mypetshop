from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Cliente

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "tu@email.com", "autofocus": True}),
    )


class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "apellidos",
            "email",
            "telefono",
            "direccion",
            "ciudad",
            "codigo_postal",
        ]
        widgets = {
            "telefono": forms.TextInput(),
            "apellidos": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in [
            "nombre",
            "apellidos",
            "email",
            "telefono",
            "direccion",
            "ciudad",
            "codigo_postal",
        ]:
            self.fields[field_name].required = True

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if Cliente.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un cliente con este email.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este email.")
        return email

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get("password1")
        pwd2 = cleaned.get("password2")
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        cliente = super().save(commit=False)
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        user = User.objects.create_user(username=email, email=email, password=password)
        cliente.user = user
        cliente.email = email
        if commit:
            cliente.save()
        return cliente


class ClienteEnvioForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "apellidos", "telefono", "direccion", "ciudad", "codigo_postal"]
        widgets = {
            "direccion": forms.TextInput(attrs={"placeholder": "C/ Principal 123"}),
            "codigo_postal": forms.TextInput(attrs={"placeholder": "28001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ["nombre", "direccion", "ciudad", "codigo_postal"]
        for field in required_fields:
            self.fields[field].required = True


class SeguimientoPedidoForm(forms.Form):
    numero_pedido = forms.CharField(
        label="Código de seguimiento",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Introduce tu código (MP-YYYYMMDD...)",
                "autofocus": True,
            }
        ),
    )
