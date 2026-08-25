
# Chambazo Version 2 Sprint 20 Jul- 16 Agos  2026 #

<img width="958" height="407" alt="image" src="https://github.com/user-attachments/assets/33d5f9a0-e7d6-4e1d-a55d-74fc7b840acb" />
<img width="959" height="404" alt="image" src="https://github.com/user-attachments/assets/d2943d0d-42e2-4b49-a868-d4f56b7fac68" />


## Historias de Usuario implementadas (15 HUs del Sprint 1)

| HU    | Descripción                        | Estado |
|-------|--------------------------------------|------|
| HU001 | Registro de usuario (flujo 3 pasos)  | Done |
| HU002 | Inicio de sesión por rol             | Done |
| HU003 | Recuperar contraseña (token)         | Done |
| HU004 | Cerrar sesión                        | Done |
| HU005 | Registro como Trabajador             | Done |
| HU006 | Registro como Contratista            | Done |
| HU007 | Selección de rol en registro         | Done |
| HU008 | Crear / completar perfil profesional | Done |
| HU009 | Selección de habilidades             | Done |
| HU010 | Actualizar perfil e imagen           | Done |
| HU011 | Visualizar perfil propio             | Done |
| HU012 | Buscar ofertas de trabajo            | Done |
| HU013 | Filtrar por categoría, zona, precio  | Done |
| HU014 | Ver detalles completos de oferta     | Done |
| HU015 | Notificaciones del sistema           | Done |
| HU016 | Aplicar a vacante con mensaje        | Done |
| HU017 | Aplicación rápida (1 clic)           | Done |
| HU018 | Confirmación de postulación          | Done |
| HU019 | Historial de solicitudes + timeline  | Done |
| HU020 | Estado de vacante (disp/proceso/ocup)| Done |

## Instalar y correr

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# Abrir: http://127.0.0.1:8000
```

## Usuarios demo

| Rol         | Email                        | Contraseña |
|-------------|------------------------------|------------|
| Trabajador  | carlos@gmail.com             | demo1234   |
| Trabajador  | ana@gmail.com                | demo1234   |
| Contratista | empresa@constructora.com     | demo1234   |
| Contratista | juan@perez.com               | demo1234   |
| Admin       | admin@chambazo.com           | admin123   |

## Stack

- **Backend:** Django 4.2 + Python 3
- **Frontend:** Bootstrap 5.3 + Bootstrap Icons + CSS custom
- **DB:** SQLite (lista para migrar a PostgreSQL)
- **Auth:** Sistema propio con roles Trabajador/Contratista
- **Admin:** /admin/

## Funcionalidades destacadas

- Registro en 3 pasos con selección de rol y habilidades
- Búsqueda full-text + filtros avanzados (categoría, zona, precio, estado)
- Aplicación normal (con mensaje) o rápida (1 clic)
- Timeline de seguimiento de solicitudes en tiempo real
- Notificaciones del sistema al contratista y trabajador
- Panel contratista con gestión de candidatos y cambio de estado
- Recuperación de contraseña con token temporal (2h)
- Perfiles con foto, habilidades, galería y reseñas
- Trabajos urgentes con banner y sección dedicada
- Asistente de chat inteligente

  Chambazo — Sprint 2 (rediseño completo según PDF)
Instalación
bash
tar -xzf chambazo_final.tar.gz
cd chambazo
pip install django pillow
python manage.py runserver

Abrir → http://127.0.0.1:8000

Cuentas de prueba
Rol	Email	Contraseña
Qué cambió en esta vuelta

Layout de dashboard con sidebar oscuro (navy) — ya no es mobile con bottom-nav
Sidebar verde para trabajador, amarillo/dorado para empleador ("Chambazo Pro")
Login y registro en pantalla dividida (panel oscuro + formulario)
Tablas de datos (Mis solicitudes, Candidatos, Publicaciones) igual al PDF
Todas las páginas nuevas del PDF: Guardados, Mensajes, Ganancias, Logros, Estadísticas, Mi empresa

Google Maps con direcciones aleatorias reales:

Mapa interactivo en "Buscar empleos" con buscador, filtro urgentes, vista satélite Mapa en cada detalle de trabajo con círculo de radio aproximado Selector de ubicación (click en mapa) al publicar una vacante. Los trabajos se generan con coordenadas aleatorias reales de 20 ciudades de El Salvador

Términos y Política de Privacidad — página completa para ambos roles (trabajador/empleador), con botón "He leído y acepto"

Chatbot generador de respuestas real — motor de reglas en Python del lado del servidor (sin depender de API externa), que consulta la base de datos en vivo: trabajos mejor pagados, % de completitud de perfil, ganancias del mes, estadísticas de vacantes, etc.

Funcionalidades extra no pedidas en el Sprint original:

Sistema de Logros/gamificación con puntos y niveles
Guardados (favoritos) con botón de corazón
Ganancias con gráfica de barras por semana
Estadísticas para empleador con gráficas de vistas vs aplicaciones y por categoría
Buscar trabajadores — el empleador puede invitar directamente a candidatos
Chat en tiempo real entre trabajador y empleador tras ser aceptado
Propuesta de tarifa personalizada al aplicar a un trabajo
