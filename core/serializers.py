from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Trabajo, Solicitud, Resena, GaleriaItem, Notificacion


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    nombre_display = serializers.CharField(read_only=True)
    completitud_perfil = serializers.IntegerField(read_only=True)
    estrellas = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'rol', 'telefono', 'ubicacion', 'lat', 'lng',
            'descripcion', 'habilidades', 'empresa', 'foto', 'verificado',
            'calificacion', 'total_trabajos', 'disponible', 'tarifa_hora',
            'experiencia_anos', 'portfolio_url', 'nombre_display',
            'completitud_perfil', 'estrellas'
        ]


class GaleriaItemSerializer(serializers.ModelSerializer):
    trabajador_nombre = serializers.CharField(source='trabajador.get_full_name', read_only=True)

    class Meta:
        model = GaleriaItem
        fields = ['id', 'trabajador', 'trabajador_nombre', 'titulo', 'descripcion', 'categoria', 'imagen', 'creado']
        read_only_fields = ['trabajador', 'creado']


class ResenaSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.CharField(source='autor.get_full_name', read_only=True)
    destinatario_nombre = serializers.CharField(source='destinatario.get_full_name', read_only=True)
    estrellas = serializers.CharField(read_only=True)

    class Meta:
        model = Resena
        fields = [
            'id', 'trabajo', 'solicitud', 'autor', 'autor_nombre',
            'destinatario', 'destinatario_nombre', 'calificacion',
            'comentario', 'etiquetas', 'estrellas', 'creado'
        ]
        read_only_fields = ['autor', 'creado']


class TrabajoSerializer(serializers.ModelSerializer):
    contratista_nombre = serializers.CharField(source='contratista.profile.nombre_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    modalidad_display = serializers.CharField(source='get_modalidad_display', read_only=True)
    candidatos_count = serializers.IntegerField(read_only=True)
    icono_categoria = serializers.CharField(read_only=True)

    class Meta:
        model = Trabajo
        fields = [
            'id', 'contratista', 'contratista_nombre', 'titulo', 'categoria',
            'categoria_display', 'descripcion', 'requisitos', 'beneficios',
            'ubicacion', 'lat', 'lng', 'presupuesto', 'es_urgente',
            'estado_vacante', 'activo', 'modalidad', 'modalidad_display',
            'duracion', 'verificacion_requerida', 'habilidades_req',
            'candidatos_count', 'icono_categoria', 'creado', 'actualizado'
        ]
        read_only_fields = ['contratista', 'creado', 'actualizado']


class SolicitudSerializer(serializers.ModelSerializer):
    trabajo_titulo = serializers.CharField(source='trabajo.titulo', read_only=True)
    trabajador_nombre = serializers.CharField(source='trabajador.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            'id', 'trabajo', 'trabajo_titulo', 'trabajador', 'trabajador_nombre',
            'estado', 'estado_display', 'mensaje', 'rapida', 'tarifa_propuesta',
            'creado', 'actualizado'
        ]
        read_only_fields = ['trabajador', 'creado', 'actualizado']
