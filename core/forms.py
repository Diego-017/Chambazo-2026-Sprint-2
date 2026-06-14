from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, Trabajo, Resena, Solicitud, SKILL_CHOICES, CATEGORY_CHOICES

# ── HU002 – Inicio de sesión ───────────────────────────────────────────────
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'}))
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))

# ── HU007 – Selección de rol ───────────────────────────────────────────────
class RegistroStep1Form(forms.Form):
    rol = forms.ChoiceField(choices=[('trabajador', 'Trabajador'), ('contratista', 'Contratista')])

# ── HU005 – Registro Trabajador ────────────────────────────────────────────
class RegistroTrabajadorForm(forms.Form):
    nombre = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Carlos Rodríguez'}))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'carlos@email.com'}))
    telefono = forms.CharField(max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '7890-1234'}))
    ubicacion = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'San Miguel, El Salvador'}))
    password = forms.CharField(label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))
    password2 = forms.CharField(label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

# ── HU006 – Registro Contratista ──────────────────────────────────────────
class RegistroContratistaForm(forms.Form):
    empresa = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mi Empresa S.A.'}))
    nombre = forms.CharField(max_length=100, label='Nombre de contacto',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan Pérez'}))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'empresa@correo.com'}))
    telefono = forms.CharField(max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+503 7123-4567'}))
    ubicacion = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'San Salvador, El Salvador'}))
    password = forms.CharField(label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))
    password2 = forms.CharField(label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

# ── HU009 – Habilidades (paso 3 registro trabajador) ─────────────────────
class HabilidadesForm(forms.Form):
    habilidades = forms.MultipleChoiceField(
        choices=SKILL_CHOICES, widget=forms.CheckboxSelectMultiple(), required=False)
    terminos = forms.BooleanField(required=True, label='Acepto los Términos y Condiciones')

# ── Paso 3 contratista ───────────────────────────────────────────────────
class DescripcionEmpresaForm(forms.Form):
    descripcion = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
            'placeholder': 'Cuéntanos sobre tu empresa, qué tipo de trabajos sueles necesitar...'}))
    terminos = forms.BooleanField(required=True, label='Acepto los Términos y Condiciones')

# ── HU003 – Recuperar contraseña ──────────────────────────────────────────
class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'}))

class NuevaPasswordForm(forms.Form):
    password = forms.CharField(label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))
    password2 = forms.CharField(label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

# ── HU008 / HU010 / HU011 – Perfil profesional + actualización ───────────
class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['foto', 'telefono', 'ubicacion', 'descripcion']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'foto': 'Foto de perfil',
            'telefono': 'Teléfono',
            'ubicacion': 'Ubicación',
            'descripcion': 'Descripción profesional',
        }

class HabilidadesUpdateForm(forms.Form):
    habilidades = forms.MultipleChoiceField(
        choices=SKILL_CHOICES, widget=forms.CheckboxSelectMultiple(), required=False)

# ── HU012 / HU013 – Búsqueda y filtro de ofertas ─────────────────────────
class BuscarOfertasForm(forms.Form):
    q = forms.CharField(required=False, label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar trabajos...'}))
    categoria = forms.ChoiceField(required=False, label='Categoría',
        choices=[('', 'Todas las categorías')] + CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}))
    ubicacion = forms.CharField(required=False, label='Zona/Ciudad',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: San Salvador'}))
    precio_min = forms.DecimalField(required=False, label='Precio mínimo', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    precio_max = forms.DecimalField(required=False, label='Precio máximo', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '500'}))
    solo_disponibles = forms.BooleanField(required=False, label='Solo disponibles',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

# ── HU016 / HU017 – Aplicar a vacante / Aplicación rápida ────────────────
class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                'placeholder': 'Cuéntale al empleador por qué eres el candidato ideal...'}),
        }
        labels = {'mensaje': 'Mensaje de presentación (opcional)'}

# ── Publicar / editar trabajo (Contratista) ───────────────────────────────
class TrabajoForm(forms.ModelForm):
    class Meta:
        model = Trabajo
        fields = ['titulo', 'categoria', 'descripcion', 'requisitos', 'beneficios',
                  'ubicacion', 'presupuesto', 'es_urgente', 'estado_vacante', 'habilidades_req']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Instalación eléctrica'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requisitos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                'placeholder': 'Requisitos mínimos del candidato...'}),
            'beneficios': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                'placeholder': 'Beneficios adicionales...'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'presupuesto': forms.NumberInput(attrs={'class': 'form-control'}),
            'es_urgente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estado_vacante': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['habilidades_req'] = forms.MultipleChoiceField(
            choices=SKILL_CHOICES, widget=forms.CheckboxSelectMultiple(), required=False,
            label='Habilidades requeridas')
        if self.instance.pk:
            self.fields['habilidades_req'].initial = self.instance.habilidades_req

    def clean_habilidades_req(self):
        return list(self.cleaned_data.get('habilidades_req', []))

# ── Reseña ────────────────────────────────────────────────────────────────
class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ['calificacion', 'comentario']
        widgets = {
            'calificacion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
