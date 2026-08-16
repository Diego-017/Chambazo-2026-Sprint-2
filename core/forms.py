from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Trabajo, SKILL_CHOICES


class LoginForm(forms.Form):
    email    = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))


class RegistroStep2Form(forms.Form):
    def __init__(self, *args, rol='trabajador', **kwargs):
        super().__init__(*args, **kwargs)
        self.rol = rol
        self.fields['nombre'] = forms.CharField(max_length=60, label='Nombre completo',
            widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Juan Pérez'}))
        self.fields['email'] = forms.EmailField(label='Correo electrónico',
            widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'correo@ejemplo.com'}))
        self.fields['telefono'] = forms.CharField(max_length=20, required=False, label='Teléfono',
            widget=forms.TextInput(attrs={'class':'form-control','placeholder':'+503 7123-4567'}))
        self.fields['ubicacion'] = forms.CharField(max_length=100, required=False, label='Ubicación',
            widget=forms.TextInput(attrs={'class':'form-control','placeholder':'San Salvador'}))
        self.fields['password'] = forms.CharField(min_length=6, label='Contraseña',
            widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'••••••••'}))
        if rol == 'contratista':
            self.fields['empresa'] = forms.CharField(max_length=100, label='Nombre de la empresa',
                widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Constructora S.A.'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email


class RegistroStep3Form(forms.Form):
    def __init__(self, *args, rol='trabajador', **kwargs):
        super().__init__(*args, **kwargs)
        self.rol = rol
        if rol == 'contratista':
            self.fields['descripcion'] = forms.CharField(required=False,
                widget=forms.Textarea(attrs={'class':'form-control','rows':'5','placeholder':'Describe tu empresa y tipo de trabajo que contratas...'}))
        self.fields['terminos'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={'style':'width:18px;height:18px;accent-color:var(--green);flex-shrink:0;margin-top:2px;'}))


class TrabajoForm(forms.ModelForm):
    class Meta:
        model = Trabajo
        fields = ['titulo', 'categoria', 'descripcion', 'requisitos', 'beneficios',
                  'ubicacion', 'presupuesto', 'es_urgente', 'modalidad', 'duracion',
                  'verificacion_requerida']
        widgets = {
            'titulo':       forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: Instalación eléctrica residencial'}),
            'categoria':    forms.Select(attrs={'class':'form-control'}),
            'descripcion':  forms.Textarea(attrs={'class':'form-control','rows':'5','placeholder':'Describe el trabajo, materiales disponibles, horario, acceso al lugar...'}),
            'requisitos':   forms.Textarea(attrs={'class':'form-control','rows':'3','placeholder':'Experiencia, certificaciones, etc.'}),
            'beneficios':   forms.Textarea(attrs={'class':'form-control','rows':'3','placeholder':'Alimentación, transporte, bono...'}),
            'ubicacion':    forms.TextInput(attrs={'class':'form-control','placeholder':'Col. Escalón, San Salvador'}),
            'presupuesto':  forms.NumberInput(attrs={'class':'form-control','placeholder':'80 - 120','min':'0'}),
            'es_urgente':   forms.CheckboxInput(),
            'modalidad':    forms.Select(attrs={'class':'form-control'}),
            'duracion':     forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: 3 días, 1 semana'}),
            'verificacion_requerida': forms.CheckboxInput(),
        }


class EditarPerfilForm(forms.ModelForm):
    nombre   = forms.CharField(max_length=60, required=False, widget=forms.TextInput(attrs={'class':'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['foto', 'telefono', 'ubicacion', 'descripcion',
                  'empresa', 'tarifa_hora', 'experiencia_anos', 'portfolio_url']
        widgets = {
            'foto':            forms.FileInput(attrs={'class':'form-control'}),
            'telefono':        forms.TextInput(attrs={'class':'form-control','placeholder':'+503 7000-0000'}),
            'ubicacion':       forms.TextInput(attrs={'class':'form-control','placeholder':'Ciudad, departamento'}),
            'descripcion':     forms.Textarea(attrs={'class':'form-control','rows':'3','placeholder':'Cuéntanos sobre ti...'}),
            'empresa':         forms.TextInput(attrs={'class':'form-control','placeholder':'Nombre de tu empresa'}),
            'tarifa_hora':     forms.NumberInput(attrs={'class':'form-control','placeholder':'0.00','min':'0'}),
            'experiencia_anos':forms.NumberInput(attrs={'class':'form-control','min':'0','max':'50'}),
            'portfolio_url':   forms.URLInput(attrs={'class':'form-control','placeholder':'https://...'}),
        }

    def __init__(self, *args, rol='trabajador', **kwargs):
        super().__init__(*args, **kwargs)
        self.rol = rol
        if rol == 'contratista':
            del self.fields['tarifa_hora']
            del self.fields['experiencia_anos']
            del self.fields['portfolio_url']
