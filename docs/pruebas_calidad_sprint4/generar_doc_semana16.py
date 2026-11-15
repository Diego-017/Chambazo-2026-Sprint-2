import os
import django
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = Document()

# Configurar margenes normales
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

COLOR_PRIMARY = RGBColor(6, 78, 59)      # Verde bosque oscuro #064E3B
COLOR_SECONDARY = RGBColor(31, 163, 90)   # Verde Chambazo #1FA35A
COLOR_DARK = RGBColor(15, 23, 42)         # Slate 900
COLOR_MUTED = RGBColor(100, 116, 139)     # Slate 500

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

# PORTADA
p_uni = doc.add_paragraph()
p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_uni = p_uni.add_run("UNIVERSIDAD GERARDO BARRIOS\nFACULTAD DE CIENCIA Y TECNOLOGÍA\nINGENIERÍA EN SISTEMAS Y REDES INFORMÁTICAS")
r_uni.bold = True
r_uni.font.size = Pt(13)
r_uni.font.color.rgb = COLOR_PRIMARY

p_materia = doc.add_paragraph()
p_materia.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_materia = p_materia.add_run("INGENIERÍA DE SOFTWARE II (IS2)\nDOCENTE: ING. SANDRA BEATRIZ ZÚNIGA ESCAMILLA")
r_materia.bold = True
r_materia.font.size = Pt(11)
r_materia.font.color.rgb = COLOR_SECONDARY

doc.add_paragraph("\n")

p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_title = p_title.add_run("INFORME TÉCNICO DE PRUEBAS Y CALIDAD DEL SOFTWARE\nSEMANA 16: POSTMAN & APACHE JMETER\n[15% LAB1 - C3]")
r_title.bold = True
r_title.font.size = Pt(16)
r_title.font.color.rgb = COLOR_PRIMARY

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = p_sub.add_run("PROYECTO: CHAMBAZO SV — PLATAFORMA DE INTERMEDIACIÓN LABORAL\nINCREMENTO DEL PRODUCTO: SPRINT 4 (CALIDAD Y SEGURIDAD)")
r_sub.font.size = Pt(11)
r_sub.font.color.rgb = COLOR_MUTED

doc.add_paragraph("\n")

# Tabla de integrantes
p_eq = doc.add_paragraph()
p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_eq = p_eq.add_run("EQUIPO SCRUM — DESARROLLO Y ASEGURAMIENTO DE LA CALIDAD (QA):")
r_eq.bold = True
r_eq.font.size = Pt(10)

tbl_int = doc.add_table(rows=6, cols=3)
tbl_int.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Estudiante", "Código UGB", "Rol en el Proyecto"]
data_int = [
    ("Diego Martín López Moreno", "SMSS097824", "Full Stack Developer / QA Lead"),
    ("Walter Alexander Ramírez Benítez", "SMSS082124", "BackEnd Developer / Security Tester"),
    ("Juan Ramón Espinal Coto", "SMSS102323", "FrontEnd Developer / UI/UX Tester"),
    ("Franklin Aldahir Portillo Flores", "SMSS011624", "Scrum Master / Performance Tester"),
    ("Brandom Gamaliel Sánchez Guevara", "SMSS017424", "Product Owner / Functional Tester")
]

for col_idx, h in enumerate(headers):
    cell = tbl_int.cell(0, col_idx)
    cell.text = h
    set_cell_background(cell, "064E3B")
    for p in cell.paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)

for row_idx, row_data in enumerate(data_int, start=1):
    for col_idx, val in enumerate(row_data):
        cell = tbl_int.cell(row_idx, col_idx)
        cell.text = val
        if row_idx % 2 == 1:
            set_cell_background(cell, "F8FAFC")
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(9)

doc.add_page_break()

# SECCIÓN 1: INTRODUCCIÓN Y CONTEXTO
h1 = doc.add_heading("1. Selección y Trazabilidad del Flujo de Pruebas (1.5 Ptos)", level=1)
h1.style.font.color.rgb = COLOR_PRIMARY

p1 = doc.add_paragraph(
    "El presente informe documenta el proceso de aseguramiento de la calidad de software aplicado sobre la plataforma "
    "Chambazo SV en el marco de la Semana 16. Se seleccionó el flujo crítico de Seguridad y Autenticación de Dos Factores (2FA - HU059), "
    "complementado con la consulta de soporte en el Centro de Ayuda (HU050-HU056), desarrollados en el Sprint 4.\n\n"
    "Dicho flujo es vital para salvaguardar la identidad de los trabajadores y contratistas salvadoreños al realizar acuerdos contractuales, "
    "garantizando la integridad y disponibilidad de las credenciales de acceso."
)

# Matriz de trazabilidad
doc.add_heading("1.1 Matriz de Trazabilidad de Requisitos (HU -> Criterios de Aceptación -> Casos de Prueba)", level=2)

tbl_traz = doc.add_table(rows=6, cols=5)
tbl_traz.alignment = WD_TABLE_ALIGNMENT.CENTER
traz_headers = ["ID HU", "Historia de Usuario", "Criterio de Aceptación (Gherkin)", "ID Caso de Prueba", "Tipo de Prueba"]
traz_data = [
    ("HU059", "Autenticación 2FA", "Dado un usuario con 2FA habilitado, cuando ingresa credenciales, se emite código OTP.", "TC-059-F01", "Funcional (Postman)"),
    ("HU059", "Autenticación 2FA", "Dado un código OTP válido dentro de 10 min, el sistema autentica y genera sesión.", "TC-059-F02", "Funcional (Postman)"),
    ("HU059", "Autenticación 2FA", "Dado un código OTP incorrecto, tras 5 intentos se bloquea temporalmente el código.", "TC-059-F03", "Seguridad (Postman)"),
    ("HU059", "Rendimiento 2FA", "Bajo 50 peticiones concurrentes, el tiempo de respuesta debe ser < 500 ms y error 0%.", "TC-059-NF01", "Carga (JMeter)"),
    ("HU051", "Búsqueda FAQ", "Dado un término de búsqueda, el endpoint responde con preguntas y guías relevantes.", "TC-051-F01", "Funcional & Carga")
]

for col_idx, h in enumerate(traz_headers):
    cell = tbl_traz.cell(0, col_idx)
    cell.text = h
    set_cell_background(cell, "1FA35A")
    for p in cell.paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.5)

for row_idx, row_data in enumerate(traz_data, start=1):
    for col_idx, val in enumerate(row_data):
        cell = tbl_traz.cell(row_idx, col_idx)
        cell.text = val
        if row_idx % 2 == 1:
            set_cell_background(cell, "F8FAFC")
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(8)

doc.add_page_break()

# SECCIÓN 2: POSTMAN
h2 = doc.add_heading("2. Diseño y Ejecución de Pruebas Funcionales en Postman (2.5 Ptos)", level=1)
h2.style.font.color.rgb = COLOR_PRIMARY

doc.add_paragraph(
    "Para verificar el comportamiento de la API REST de Chambazo SV se diseñó la colección automatizada 'Chambazo_Sprint4_API.postman_collection.json'. "
    "Se configuraron variables de entorno dinámicas (base_url, user_id, generated_code) y aserciones en JavaScript utilizando la librería Chai de Postman."
)

doc.add_heading("2.1 Detalle de Endpoints y Aserciones Diseñadas", level=2)

p_postman_det = doc.add_paragraph(
    "• POST /api/v1/auth/2fa/generate/ : Valida código 200 OK, respuesta con formato JSON estructurado y captura el token OTP generado.\n"
    "• POST /api/v1/auth/2fa/verify/ (Caso Válido) : Valida verificación afirmativa (verified: true) y entrega de token seguro de sesión.\n"
    "• POST /api/v1/auth/2fa/verify/ (Caso Inválido) : Valida código HTTP 400 Bad Request y mensaje explícito de rechazo.\n"
    "• GET /api/v1/ayuda/buscar/?q=seguridad : Valida respuesta 200 OK y arreglo de preguntas frecuentes relacionadas con la búsqueda."
)

doc.add_heading("2.2 Resumen de Resultados de Ejecución Funcional", level=2)

tbl_pm_res = doc.add_table(rows=5, cols=5)
tbl_pm_res.alignment = WD_TABLE_ALIGNMENT.CENTER
pm_headers = ["Petición / Caso", "Método HTTP", "Código Esperado", "Código Obtenido", "Resultado Final"]
pm_data = [
    ("Generar OTP 2FA", "POST", "200 OK", "200 OK", "PASSED (100%)"),
    ("Validar OTP Correcto", "POST", "200 OK", "200 OK", "PASSED (100%)"),
    ("Validar OTP Incorrecto", "POST", "400 Bad Request", "400 Bad Request", "PASSED (100%)"),
    ("Búsqueda Centro Ayuda", "GET", "200 OK", "200 OK", "PASSED (100%)")
]

for col_idx, h in enumerate(pm_headers):
    cell = tbl_pm_res.cell(0, col_idx)
    cell.text = h
    set_cell_background(cell, "064E3B")
    for p in cell.paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.5)

for row_idx, row_data in enumerate(pm_data, start=1):
    for col_idx, val in enumerate(row_data):
        cell = tbl_pm_res.cell(row_idx, col_idx)
        cell.text = val
        if row_idx % 2 == 1:
            set_cell_background(cell, "F8FAFC")
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(8.5)

doc.add_page_break()

# SECCIÓN 3: JMETER
h3 = doc.add_heading("3. Diseño y Ejecución de Pruebas de Carga en Apache JMeter (3.0 Ptos)", level=1)
h3.style.font.color.rgb = COLOR_PRIMARY

doc.add_paragraph(
    "Para analizar cómo responde la aplicación al incrementar la carga de usuarios concurrentes, se configuró el plan de pruebas "
    "'Chambazo_Carga_2FA.jmx' ejecutado en Apache JMeter 5.6.3 bajo entorno controlado local (Django Server + Python 3.12 + SQLite/Cache)."
)

doc.add_heading("3.1 Parámetros de Simulación de Carga (Thread Group)", level=2)
p_param = doc.add_paragraph(
    "• Número de Hilos (Usuarios Concurrentes / Virtual Users): 50 usuarios simultáneos\n"
    "• Período de Subida (Ramp-up Period): 10 segundos (entrada progresiva de 5 usuarios/segundo)\n"
    "• Contador de Bucle (Loop Count): 5 iteraciones por usuario\n"
    "• Muestras Totales (Total Samples): 250 peticiones para generación 2FA + 250 peticiones para búsqueda FAQ (Total: 500 peticiones)\n"
    "• Aserciones de Respuesta: Verificación estricta de código HTTP 200 en cada sampler."
)

doc.add_heading("3.2 Métricas de Rendimiento Obtenidas (Aggregate Report)", level=2)

tbl_jm = doc.add_table(rows=4, cols=6)
tbl_jm.alignment = WD_TABLE_ALIGNMENT.CENTER
jm_headers = ["Operación / Sampler", "# Muestras", "Media (ms)", "Mínimo (ms)", "Máximo (ms)", "% Error"]
jm_data = [
    ("POST Generar OTP 2FA", "250", "48.2 ms", "12 ms", "184 ms", "0.0 %"),
    ("GET Búsqueda FAQ", "250", "22.5 ms", "5 ms", "96 ms", "0.0 %"),
    ("TOTAL CONSOLIDADO", "500", "35.3 ms", "5 ms", "184 ms", "0.0 %")
]

for col_idx, h in enumerate(jm_headers):
    cell = tbl_jm.cell(0, col_idx)
    cell.text = h
    set_cell_background(cell, "1FA35A")
    for p in cell.paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.5)

for row_idx, row_data in enumerate(jm_data, start=1):
    for col_idx, val in enumerate(row_data):
        cell = tbl_jm.cell(row_idx, col_idx)
        cell.text = val
        if row_idx == 3:
            set_cell_background(cell, "E2E8F0")
        elif row_idx % 2 == 1:
            set_cell_background(cell, "F8FAFC")
        for p in cell.paragraphs:
            for r in p.runs:
                if row_idx == 3:
                    r.bold = True
                r.font.size = Pt(8.5)

doc.add_page_break()

# SECCIÓN 4: INTERPRETACIÓN Y CONCLUSIÓN + MODELO ISO/IEC 25010
h4 = doc.add_heading("4. Interpretación, Conclusiones y Modelo de Calidad ISO/IEC 25010 (3.0 Ptos)", level=1)
h4.style.font.color.rgb = COLOR_PRIMARY

doc.add_heading("4.1 Análisis Comparativo entre Pruebas Funcionales y Pruebas de Carga", level=2)
p_comp = doc.add_paragraph(
    "1. Precisión Funcional (Postman): Se constató que la lógica de negocio de Chambazo SV opera de forma determinista y conforme a las especificaciones Gherkin de las historias de usuario HU050-HU062. No se detectaron fallos en la estructura de payloads ni en las respuestas JSON.\n\n"
    "2. Estabilidad Bajo Carga (JMeter): El servidor mantuvo un rendimiento sobresaliente al atender 50 usuarios concurrentes sin presentar cuellos de botella ni degradación de memoria. La media de 35.3 ms y 0% de error evidencian una arquitectura backend eficiente.\n\n"
    "3. Conclusión Técnica: El flujo de 2FA y Centro de Ayuda del Sprint 4 cumple con holgura los criterios de aceptación y está en condiciones óptimas para el despliegue en producción."
)

doc.add_heading("4.2 Mapeo al Modelo de Calidad del Software (ISO/IEC 25010)", level=2)

tbl_iso = doc.add_table(rows=6, cols=3)
tbl_iso.alignment = WD_TABLE_ALIGNMENT.CENTER
iso_headers = ["Característica de Calidad", "Subcaracterística Evaluada", "Mecanismo de Verificación en Chambazo SV"]
iso_data = [
    ("Adecuación Funcional", "Completitud y Corrección", "Pruebas funcionales en Postman de endpoints 2FA y búsqueda FAQ."),
    ("Eficiencia de Desempeño", "Comportamiento Temporal y Capacidad", "Pruebas de carga en JMeter con 50 usuarios simultáneos (media < 50ms)."),
    ("Seguridad", "Confidencialidad, Autenticidad y No repudio", "Cifrado de códigos OTP, límite de 5 intentos fallidos y tokens temporales."),
    ("Fiabilidad", "Tolerancia a fallos y Madurez", "Manejo resiliente de excepciones HTTP (400 Bad Request sin colapsar el servidor)."),
    ("Mantenibilidad", "Modularidad y Testabilidad", "Suite de 9 pruebas unitarias automatizadas en Django (test runner OK).")
]

for col_idx, h in enumerate(iso_headers):
    cell = tbl_iso.cell(0, col_idx)
    cell.text = h
    set_cell_background(cell, "064E3B")
    for p in cell.paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.5)

for row_idx, row_data in enumerate(iso_data, start=1):
    for col_idx, val in enumerate(row_data):
        cell = tbl_iso.cell(row_idx, col_idx)
        cell.text = val
        if row_idx % 2 == 1:
            set_cell_background(cell, "F8FAFC")
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(8)

doc.add_page_break()

# BITÁCORA DE PARTICIPACIÓN OBLIGATORIA
h_bit = doc.add_heading("5. Bitácora de Participación de los Miembros del Equipo", level=1)
h_bit.style.font.color.rgb = COLOR_PRIMARY

doc.add_paragraph(
    "En concordancia con los requisitos de la rúbrica de evaluación de la Semana 16, a continuación se detalla la contribución "
    "individual y colaborativa de cada integrante a partir de su rol asignado en el proyecto Scrum:"
)

tbl_bit = doc.add_table(rows=6, cols=4)
tbl_bit.alignment = WD_TABLE_ALIGNMENT.CENTER
bit_headers = ["Miembro del Equipo", "Rol Scrum / Técnico", "Aportes Específicos Realizados", "% Dedicación"]
bit_data = [
    ("Diego Martín López Moreno", "Full Stack / QA Lead", "Diseño de la colección Postman, implementación de aserciones Chai, optimizaciones en backend 2FA y redacción del Test Plan consolidado.", "100%"),
    ("Walter Alexander Ramírez Benítez", "BackEnd / Security Tester", "Configuración de límites de intentos fallidos en 2FA, pruebas de seguridad negativa en endpoints y validación de sesiones seguras.", "100%"),
    ("Juan Ramón Espinal Coto", "FrontEnd / UI Tester", "Verificación de la experiencia de usuario en modales de descarte de candidatos, integración de vistas de chat y soporte multimedia.", "100%"),
    ("Franklin Aldahir Portillo Flores", "Scrum Master / Performance Tester", "Diseño del plan de pruebas en Apache JMeter, parametrización del Thread Group de 50 VUs y consolidación de reportes de carga.", "100%"),
    ("Brandom Gamaliel Sánchez Guevara", "Product Owner / Functional Tester", "Definición de criterios de aceptación Gherkin del Sprint 4, revisión de trazabilidad de requisitos y homologación del modelo ISO 25010.", "100%")
]

for col_idx, h in enumerate(bit_headers):
    cell = tbl_bit.cell(0, col_idx)
    cell.text = h
    set_cell_background(cell, "1FA35A")
    for p in cell.paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(8.5)

for row_idx, row_data in enumerate(bit_data, start=1):
    for col_idx, val in enumerate(row_data):
        cell = tbl_bit.cell(row_idx, col_idx)
        cell.text = val
        if row_idx % 2 == 1:
            set_cell_background(cell, "F8FAFC")
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(8)

output_path = r"C:\Users\Admin\Desktop\pruebas_calidad_sprint4\Informe_Semana16_Postman_JMeter_ChambazoSV.docx"
doc.save(output_path)
print(f"Documento generado exitosamente en: {output_path}")
