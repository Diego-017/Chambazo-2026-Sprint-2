<<<<<<< HEAD
# Chambazo-2026-Version 2 Julio 2026
=======
# 🟢 Chambazo — Django + Python | Sprint 1 Completo

## Historias de Usuario implementadas (15 HUs del Sprint 1)

| HU    | Descripción                          | Estado  |
|-------|--------------------------------------|---------|
| HU001 | Registro de usuario (flujo 3 pasos)  | ✅ Done |
| HU002 | Inicio de sesión por rol             | ✅ Done |
| HU003 | Recuperar contraseña (token)         | ✅ Done |
| HU004 | Cerrar sesión                        | ✅ Done |
| HU005 | Registro como Trabajador             | ✅ Done |
| HU006 | Registro como Contratista            | ✅ Done |
| HU007 | Selección de rol en registro         | ✅ Done |
| HU008 | Crear / completar perfil profesional | ✅ Done |
| HU009 | Selección de habilidades             | ✅ Done |
| HU010 | Actualizar perfil e imagen           | ✅ Done |
| HU011 | Visualizar perfil propio             | ✅ Done |
| HU012 | Buscar ofertas de trabajo            | ✅ Done |
| HU013 | Filtrar por categoría, zona, precio  | ✅ Done |
| HU014 | Ver detalles completos de oferta     | ✅ Done |
| HU015 | Notificaciones del sistema           | ✅ Done |
| HU016 | Aplicar a vacante con mensaje        | ✅ Done |
| HU017 | Aplicación rápida (1 clic)           | ✅ Done |
| HU018 | Confirmación de postulación          | ✅ Done |
| HU019 | Historial de solicitudes + timeline  | ✅ Done |
| HU020 | Estado de vacante (disp/proceso/ocup)| ✅ Done |

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
>>>>>>> e69eda2 (Subiendo proyecto)
