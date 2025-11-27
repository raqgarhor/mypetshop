from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Cliente, Producto, Marca, Categoria

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


class ClienteAdminForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Dejar en blanco si no quieres cambiar la contraseña."
    )
    
    class Meta:
        model = Cliente
        fields = [
            'nombre',
            'apellidos',
            'email',
            'telefono',
            'direccion',
            'ciudad',
            'codigo_postal',
            'es_admin',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'es_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.instance_user = None
        if 'instance' in kwargs and kwargs['instance']:
            if hasattr(kwargs['instance'], 'user') and kwargs['instance'].user:
                self.instance_user = kwargs['instance'].user
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.pk:
            # Si estamos editando, permitir el mismo email
            if Cliente.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe un cliente con este email.")
        else:
            # Si estamos creando, verificar que no exista
            if Cliente.objects.filter(email=email).exists():
                raise forms.ValidationError("Ya existe un cliente con este email.")
        return email

    def save(self, commit=True):
        cliente = super().save(commit=False)
        
        if commit:
            cliente.save()
            
            # Manejar usuario
            if not cliente.user:
                # Crear nuevo usuario
                from django.contrib.auth import get_user_model
                User = get_user_model()
                password_default = 'cliente123'
                user = User.objects.create_user(
                    username=cliente.email,
                    email=cliente.email,
                    first_name=cliente.nombre,
                    last_name=cliente.apellidos or '',
                    password=password_default,
                )
                cliente.user = user
                cliente.save()
            else:
                # Actualizar usuario existente
                cliente.user.email = cliente.email
                cliente.user.first_name = cliente.nombre
                cliente.user.last_name = cliente.apellidos or ''
                cliente.user.save()
            
            # Cambiar contraseña si se proporcionó
            password = self.cleaned_data.get('password')
            if password:
                cliente.user.set_password(password)
                cliente.user.save()
        
        return cliente


class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'descripcion',
            'precio',
            'precio_oferta',
            'marca',
            'categoria',
            'genero',
            'color',
            'material',
            'stock',
            'esta_disponible',
            'es_destacado',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'precio_oferta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'marca': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'esta_disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['marca'].queryset = Marca.objects.all().order_by('nombre')
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')
        self.fields['marca'].required = True
        self.fields['precio'].required = True
