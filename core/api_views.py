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
    queryset = GaleriaItem.objects.all().select_related('trabajador')
    serializer_class = GaleriaItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(trabajador=self.request.user)


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
