from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum
from .models import UserProfile, Trabajo, Solicitud, Resena, GaleriaItem
from .serializers import (
    UserProfileSerializer, TrabajoSerializer, SolicitudSerializer,
    ResenaSerializer, GaleriaItemSerializer
)


class TrabajoViewSet(viewsets.ModelViewSet):
    queryset = Trabajo.objects.filter(activo=True).select_related('contratista__profile')
    serializer_class = TrabajoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titulo', 'descripcion', 'ubicacion', 'categoria']
    ordering_fields = ['creado', 'presupuesto', 'vistas']

    def perform_create(self, serializer):
        serializer.save(contratista=self.request.user)


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.all().select_related('user')
    serializer_class = UserProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'ubicacion', 'empresa']

    def get_queryset(self):
        qs = super().get_queryset()
        rol = self.request.query_params.get('rol', None)
        if rol:
            qs = qs.filter(rol=rol)
        return qs


class SolicitudViewSet(viewsets.ModelViewSet):
    serializer_class = SolicitudSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Solicitud.objects.all()
        # Trabajador ve sus postulaciones, Contratista ve postulaciones a sus ofertas
        return Solicitud.objects.filter(
            trabajador=user
        ) | Solicitud.objects.filter(
            trabajo__contratista=user
        ).select_related('trabajo', 'trabajador')

    def perform_create(self, serializer):
        serializer.save(trabajador=self.request.user)


class ResenaViewSet(viewsets.ModelViewSet):
    queryset = Resena.objects.all().select_related('autor', 'destinatario', 'trabajo')
    serializer_class = ResenaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)


class GaleriaItemViewSet(viewsets.ModelViewSet):
    queryset = GaleriaItem.objects.all().select_related('usuario')
    serializer_class = GaleriaItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class PlataformaStatsAPIView(APIView):
    """Métricas generales de la plataforma para dashboards y analítica."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_trabajadores = UserProfile.objects.filter(rol='trabajador').count()
        total_contratistas = UserProfile.objects.filter(rol='contratista').count()
        total_ofertas = Trabajo.objects.filter(activo=True).count()
        total_contrataciones = Solicitud.objects.filter(estado__in=['contratado', 'completado']).count()
        promedio_calificacion = Resena.objects.aggregate(a=Avg('calificacion'))['a'] or 4.8
        presupuesto_promedio = Trabajo.objects.aggregate(a=Avg('presupuesto'))['a'] or 0

        # Categorías más demandadas
        top_categorias = Trabajo.objects.values('categoria').annotate(
            total=Count('id')
        ).order_by('-total')[:5]

        return Response({
            'total_trabajadores': total_trabajadores,
            'total_contratistas': total_contratistas,
            'total_ofertas': total_ofertas,
            'total_contrataciones': total_contrataciones,
            'promedio_calificacion': round(promedio_calificacion, 1),
            'presupuesto_promedio': round(presupuesto_promedio, 2),
            'top_categorias': list(top_categorias),
        }, status=status.HTTP_200_OK)



class CalendarioEventosAPIView(APIView):
    """Devuelve eventos del calendario en formato FullCalendar para el usuario logueado."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        eventos = []

        try:
            rol = user.profile.rol
        except Exception:
            return Response([], status=status.HTTP_200_OK)

        if rol == 'trabajador':
            solicitudes = Solicitud.objects.filter(
                trabajador=user,
                estado__in=['contratado', 'en_progreso', 'completado']
            ).select_related('trabajo', 'trabajo__contratista__profile')

            for sol in solicitudes:
                t = sol.trabajo
                color_map = {
                    'contratado': '#f59e0b',
                    'en_progreso': '#3b82f6',
                    'completado': '#10b981',
                }
                evento = {
                    'title': t.titulo,
                    'start': str(t.fecha_inicio) if t.fecha_inicio else str(t.creado.date()),
                    'end': str(t.fecha_limite) if t.fecha_limite else None,
                    'url': f'/solicitud/{sol.pk}/gestionar/',
                    'backgroundColor': color_map.get(sol.estado, '#6b7280'),
                    'borderColor': color_map.get(sol.estado, '#6b7280'),
                    'extendedProps': {
                        'empresa': t.contratista.profile.nombre_display,
                        'ubicacion': t.ubicacion,
                        'presupuesto': str(t.presupuesto),
                        'estado': sol.get_estado_display(),
                    }
                }
                eventos.append(evento)
        else:
            # Contratista
            trabajos = Trabajo.objects.filter(
                contratista=user,
                activo=True
            )
            for t in trabajos:
                estado_color = {
                    'disponible': '#3b82f6',
                    'en_proceso': '#f59e0b',
                    'ocupada': '#10b981',
                }
                evento = {
                    'title': t.titulo,
                    'start': str(t.fecha_inicio) if t.fecha_inicio else str(t.creado.date()),
                    'end': str(t.fecha_limite) if t.fecha_limite else None,
                    'url': f'/contratista/trabajo/{t.pk}/candidatos/',
                    'backgroundColor': estado_color.get(t.estado_vacante, '#6b7280'),
                    'borderColor': estado_color.get(t.estado_vacante, '#6b7280'),
                    'extendedProps': {
                        'candidatos': t.candidatos_count,
                        'ubicacion': t.ubicacion,
                        'presupuesto': str(t.presupuesto),
                        'estado': t.get_estado_vacante_display(),
                    }
                }
                eventos.append(evento)

        return Response(eventos, status=status.HTTP_200_OK)
