from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Trabajo, SKILL_CHOICES, Resena, GaleriaItem


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
        self.fields['ubicacion'] = forms.CharField(max_length=180, required=False, label='Ubicación',
            widget=forms.TextInput(attrs={'class':'form-control', 'id':'id_ubicacion', 'placeholder':'Selecciona tu ubicación', 'readonly':'readonly', 'style':'cursor:pointer;background:#fff;'}))
        self.fields['password'] = forms.CharField(min_length=6, label='Contraseña',
            widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'••••••••'}))
        self.fields['confirmar_password'] = forms.CharField(min_length=6, label='Confirmar contraseña',
            widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'••••••••'}))
        if rol == 'contratista':
            self.fields['empresa'] = forms.CharField(max_length=100, label='Nombre de la empresa',
                widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Constructora S.A.'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar_password = cleaned_data.get('confirmar_password')
        if password and confirmar_password and password != confirmar_password:
            self.add_error('confirmar_password', 'Las contraseñas no coinciden.')
        return cleaned_data


class RegistroStep3Form(forms.Form):
    def __init__(self, *args, rol='trabajador', **kwargs):
        super().__init__(*args, **kwargs)
        self.rol = rol
        if rol == 'contratista':
            self.fields['tipo_empresa'] = forms.ChoiceField(
                label='Tipo de empleador',
                choices=[
                    ('privada', 'Empresa Privada'),
                    ('publica', 'Institución Pública'),
                    ('ong', 'ONG / Sin fines de lucro'),
                    ('independiente', 'Profesional Independiente'),
                ],
                initial='privada',
                widget=forms.Select(attrs={'class': 'form-control'}))
            self.fields['descripcion'] = forms.CharField(required=False,
                widget=forms.Textarea(attrs={'class':'form-control','rows':'5','placeholder':'Describe tu empresa y tipo de trabajo que contratas...'}))
        self.fields['terminos'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={'style':'width:18px;height:18px;accent-color:var(--green);flex-shrink:0;margin-top:2px;'}))


class TrabajoForm(forms.ModelForm):
    class Meta:
        model = Trabajo
        fields = [
            'titulo', 'categoria', 'tipo_oportunidad', 'descripcion', 'requisitos', 'beneficios',
            'ubicacion', 'presupuesto', 'es_urgente', 'modalidad', 'duracion',
            'verificacion_requerida', 'fecha_inicio', 'fecha_limite',
            'nivel_experiencia', 'herramientas', 'horario', 'vacantes_disponibles',
            'transporte_propio', 'contacto_emergencia_sitio'
        ]
        widgets = {
            'titulo':       forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: Instalación eléctrica residencial'}),
            'categoria':    forms.Select(attrs={'class':'form-control'}),
            'tipo_oportunidad': forms.Select(attrs={'class':'form-control'}),
            'descripcion':  forms.Textarea(attrs={'class':'form-control','rows':'4','placeholder':'Describe el trabajo, materiales disponibles, horario, acceso al lugar...'}),
            'requisitos':   forms.Textarea(attrs={'class':'form-control','rows':'2','placeholder':'Experiencia, certificaciones, etc.'}),
            'beneficios':   forms.Textarea(attrs={'class':'form-control','rows':'2','placeholder':'Alimentación, transporte, bono...'}),
            'ubicacion':    forms.TextInput(attrs={'class':'form-control','id':'id_ubicacion_input','placeholder':'Col. Escalón, San Salvador'}),
            'presupuesto':  forms.NumberInput(attrs={'class':'form-control','id':'id_presupuesto_input','placeholder':'100.00','min':'1','step':'0.50'}),
            'es_urgente':   forms.CheckboxInput(attrs={'id':'id_es_urgente_chk'}),
            'modalidad':    forms.Select(attrs={'class':'form-control'}),
            'duracion':     forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: 3 días, 1 semana'}),
            'verificacion_requerida': forms.CheckboxInput(),
            'fecha_inicio': forms.DateInput(attrs={'class':'form-control', 'type':'date'}),
            'fecha_limite': forms.DateInput(attrs={'class':'form-control', 'type':'date'}),
            'nivel_experiencia': forms.Select(attrs={'class':'form-control'}),
            'herramientas': forms.Select(attrs={'class':'form-control'}),
            'horario': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Ej: 8:00 AM - 5:00 PM'}),
            'vacantes_disponibles': forms.NumberInput(attrs={'class':'form-control', 'min':'1'}),
            'transporte_propio': forms.CheckboxInput(),
            'contacto_emergencia_sitio': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre y teléfono de encargado en sitio'}),
        }


class EditarPerfilForm(forms.ModelForm):
    nombre   = forms.CharField(max_length=60, required=False, widget=forms.TextInput(attrs={'class':'form-control'}))

    class Meta:
        model = UserProfile
        fields = [
            'foto', 'telefono', 'ubicacion', 'descripcion',
            'empresa', 'portfolio_url',
            # Trabajador
            'dui', 'vehiculo', 'certificaciones', 'cv_pdf',
            'nivel_educativo',
            # Contratista
            'nit_nrc', 'giro_comercial', 'sitio_web', 'redes_sociales',
            'contacto_cargo', 'anos_operacion', 'cantidad_empleados', 'tipo_empresa', 'registro_fiscal'
        ]
        widgets = {
            'foto':            forms.FileInput(attrs={'class':'form-control'}),
            'cv_pdf':          forms.FileInput(attrs={'class':'form-control', 'accept': 'application/pdf'}),
            'telefono':        forms.TextInput(attrs={'class':'form-control','placeholder':'+503 7000-0000'}),
            'ubicacion':       forms.TextInput(attrs={'class':'form-control','placeholder':'Ciudad, departamento'}),
            'descripcion':     forms.Textarea(attrs={'class':'form-control','rows':'3','placeholder':'Cuéntanos sobre ti o tu empresa...'}),
            'empresa':         forms.TextInput(attrs={'class':'form-control','placeholder':'Nombre comercial de la empresa'}),
            'portfolio_url':   forms.URLInput(attrs={'class':'form-control','placeholder':'https://...'}),
            # Trabajador
            'dui':             forms.TextInput(attrs={'class':'form-control','placeholder':'01234567-8'}),
            'vehiculo':        forms.Select(attrs={'class':'form-control'}),
            'certificaciones': forms.Textarea(attrs={'class':'form-control','rows':'2','placeholder':'Ej: Licencia de conducir liviana, curso INSAFORP de electricidad (opcional)'}),
            'nivel_educativo': forms.Select(attrs={'class':'form-control'}),
            # Contratista
            'nit_nrc':         forms.TextInput(attrs={'class':'form-control','placeholder':'0614-010190-001-1 / NRC 123456'}),
            'giro_comercial':  forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: Construcción, remodelaciones y servicios residenciales'}),
            'sitio_web':       forms.URLInput(attrs={'class':'form-control','placeholder':'https://miempresa.com'}),
            'redes_sociales':  forms.TextInput(attrs={'class':'form-control','placeholder':'LinkedIn / Instagram / Facebook'}),
            'contacto_cargo':  forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: Gerente de Operaciones'}),
            'anos_operacion':  forms.NumberInput(attrs={'class':'form-control','min':'0'}),
            'cantidad_empleados': forms.Select(attrs={'class':'form-control'}),
            'tipo_empresa': forms.Select(attrs={'class':'form-control'}),
            'registro_fiscal': forms.FileInput(attrs={'class':'form-control'}),
        }

    def __init__(self, *args, rol='trabajador', **kwargs):
        super().__init__(*args, **kwargs)
        self.rol = rol
        if rol == 'contratista':
            campos_trabajador = ['tarifa_hora', 'experiencia_anos', 'portfolio_url', 'dui', 'vehiculo', 'disponibilidad_horario', 'certificaciones', 'contacto_emergencia', 'nivel_educativo', 'idiomas', 'referencias_personales', 'expectativa_salarial']
            for f in campos_trabajador:
                self.fields.pop(f, None)
        else:
            campos_contratista = ['empresa', 'nit_nrc', 'giro_comercial', 'sitio_web', 'redes_sociales', 'contacto_cargo', 'anos_operacion', 'cantidad_empleados', 'tipo_empresa', 'registro_fiscal']
            for f in campos_contratista:
                self.fields.pop(f, None)


class PagoTarjetaForm(forms.Form):
    numero_tarjeta = forms.CharField(max_length=19, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': '4000 1234 5678 9010', 'id': 'card_number', 'autocomplete': 'cc-number'
    }), label='Número de tarjeta')
    titular_tarjeta = forms.CharField(max_length=80, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'JUAN PEREZ', 'id': 'card_holder'
    }), label='Nombre del titular')
    exp_mes_ano = forms.CharField(max_length=5, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'MM/AA', 'id': 'card_exp'
    }), label='Vencimiento')
    cvc = forms.CharField(max_length=4, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': '123', 'id': 'card_cvc', 'maxlength': '4'
    }), label='CVC / CVV')


class MensajeChatForm(forms.Form):
    texto = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Escribe un mensaje...', 'id': 'chatTextInput'
    }))
    adjunto = forms.FileField(required=False, widget=forms.FileInput(attrs={'id': 'fileInput', 'style': 'display:none;'}))
    audio = forms.FileField(required=False, widget=forms.FileInput(attrs={'id': 'audioInput', 'style': 'display:none;'}))
    lat = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'latInput'}))
    lng = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'lngInput'}))
    ubicacion_nombre = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'ubicacionNombreInput'}))


class ResenaForm(forms.ModelForm):
    ETIQUETAS_OPCIONES = [
        ('Puntualidad', 'Puntualidad'),
        ('Calidad de trabajo', 'Calidad de trabajo'),
        ('Excelente comunicación', 'Excelente comunicación'),
        ('Profesionalismo', 'Profesionalismo'),
        ('Pago oportuno', 'Pago oportuno'),
        ('Trato respetuoso', 'Trato respetuoso'),
    ]

    calificacion = forms.IntegerField(min_value=1, max_value=5, initial=5,
        widget=forms.HiddenInput())
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '4',
                                     'placeholder': 'Describe tu experiencia de trabajo, aspectos destacados o recomendaciones...'}),
        label='Tu reseña')

    class Meta:
        model = Resena
        fields = ['calificacion', 'comentario']


class GaleriaItemForm(forms.ModelForm):
    class Meta:
        model = GaleriaItem
        fields = ['titulo', 'categoria', 'descripcion', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Instalación de panel eléctrico'}),
            'categoria': forms.Select(choices=SKILL_CHOICES, attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'Detalles del trabajo realizado, materiales o técnicas...'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }