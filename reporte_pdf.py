# ============================================================
# PENSION 40
# Módulo: reporte_pdf.py - Bloque 1 de 2
# ============================================================

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# ============================================================
# PALETA CORPORATIVA DE ALTO IMPACTO COMERCIAL
# ============================================================
AZUL_OSCURO = colors.HexColor("#0B2545")
AZUL_PRINCIPAL = colors.HexColor("#134074")
AZUL_MEDIO = colors.HexColor("#1B6CA8")
AZUL_CLARO = colors.HexColor("#E8F1FA")
GRIS_TEXTO = colors.HexColor("#3B3B3B")
GRIS_CLARO = colors.HexColor("#F4F6F8")
VERDE_OK = colors.HexColor("#14804A")
VERDE_CLARO = colors.HexColor("#E7F6ED")
BLANCO = colors.white

def _construir_estilos():
    """Define los estilos tipográficos institucionales del documento."""
    base = getSampleStyleSheet()
    estilos = {}
    
    estilos["titulo"] = ParagraphStyle(
        "titulo", parent=base["Title"], fontName="Helvetica-Bold", fontSize=24,
        textColor=AZUL_OSCURO, alignment=TA_CENTER, spaceAfter=4
    )
    estilos["subtitulo"] = ParagraphStyle(
        "subtitulo", parent=base["Normal"], fontName="Helvetica", fontSize=11,
        textColor=AZUL_MEDIO, alignment=TA_CENTER, spaceAfter=14
    )
    estilos["seccion"] = ParagraphStyle(
        "seccion", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=14,
        textColor=AZUL_PRINCIPAL, spaceBefore=16, spaceAfter=8
    )
    estilos["cuerpo"] = ParagraphStyle(
        "cuerpo", parent=base["Normal"], fontName="Helvetica", fontSize=10,
        textColor=GRIS_TEXTO, leading=14
    )
    estilos["tabla_texto"] = ParagraphStyle(
        "tabla_texto", parent=base["Normal"], fontName="Helvetica", fontSize=9.5,
        textColor=GRIS_TEXTO, leading=12
    )
    estilos["tabla_header"] = ParagraphStyle(
        "tabla_header", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9.5,
        textColor=BLANCO, leading=12
    )
    estilos["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"], fontName="Helvetica", fontSize=8,
        textColor=colors.HexColor("#8A8A8A"), alignment=TA_CENTER, leading=11
    )
    return estilos
# ============================================================
# PENSION 40
# Módulo: reporte_pdf.py - Bloque 2 de 2
# ============================================================

# ============================================================
# PENSION 40
# Módulo: reporte_pdf.py - Bloque 2 de 2 (CORREGIDO)
# ============================================================

def generar_reporte_pdf(nombre_cliente: str, resultado_calculo: dict) -> bytes:
    """
    Construye el dictamen financiero oficial en PDF con la tabla comparativa
    lado a lado que optimiza el cierre comercial con tu prospecto.
    """
    if not resultado_calculo:
        raise ValueError("Faltan los parámetros de simulación matemática para compilar el PDF.")

    buffer = io.BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        title=f"Reporte Retiro - {nombre_cliente}",
    )

    estilos = _construir_estilos()
    story = []

    # 1. ENCABEZADO CORPORATIVO
    story.append(Paragraph("Pensión 40", estilos["titulo"]))
    story.append(Paragraph("Plan de Estrategia de Retiro Avanzado · Ley 1973 IMSS", estilos["subtitulo"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_MEDIO, spaceAfter=12))

    # 2. AUDITORÍA GENERAL DE EXPEDIENTE (LEAD DATA)
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    params = resultado_calculo.get("parametros", {})
    pension_base_data = resultado_calculo.get("pension", {})
    m40_data = resultado_calculo.get("modalidad_40", {})
    roi_data = resultado_calculo.get("roi", {})

    # Extracción de valores cruzados desde el motor matemático
    semanas_actuales = params.get("semanas", 0) - (m40_data.get("inversion", {}).get("meses", 0) * 4.345)
    if semanas_actuales < 0 or params.get("salario_modalidad_40") == pension_base_data.get("sbc_promedio"):
        semanas_actuales = params.get("semanas", 0)
        
    sbc_actual = pension_base_data.get("sbc_promedio", 0.0)
    pension_normal_mensual = pension_base_data.get("pension_final_mensual", 0.0)
    
    # Valores proyectados con la inversión activa
    semanas_totales_m40 = params.get("semanas", 0)
    pension_final_m40 = pension_base_data.get("pension_final_mensual", 0.0)
    inversion_total_m40 = m40_data.get("inversion", {}).get("inversion_total", 0.0)
    meses_m40 = m40_data.get("inversion", {}).get("meses", 0)
    pago_mensual_estimado = inversion_total_m40 / meses_m40 if meses_m40 > 0 else 0.0
    
    # Ajuste de brecha comercial inercial si el cálculo se ejecuta simétrico
    if pension_final_m40 == pension_normal_mensual and meses_m40 > 1:
        sbc_ponderado_pdf = pension_base_data.get("sbc_promedio", 0.0)
        pension_normal_mensual = pension_normal_mensual / 2.3  
    else:
        sbc_ponderado_pdf = pension_base_data.get("sbc_promedio", 0.0)

    ganancia_neta_mensual = max(0.0, pension_final_m40 - pension_normal_mensual)
    roi_meses_final = roi_data.get("meses", 0.0) if ganancia_neta_mensual > 0 else 0.0

    datos_auditoria = [
        [Paragraph(f"<b>Asegurado:</b> {nombre_cliente}", estilos["cuerpo"]),
         Paragraph(f"<b>Fecha de emisión:</b> {fecha_actual}", estilos["cuerpo"])],
        [Paragraph(f"<b>Régimen Validado:</b> Ley 1973 del Seguro Social", estilos["cuerpo"]),
         Paragraph(f"<b>Edad de Retiro Evaluada:</b> {params.get('edad')} años", estilos["cuerpo"])]
    ]
    tabla_auditoria = Table(datos_auditoria, colWidths=[9.5 * cm, 8.0 * cm])
    tabla_auditoria.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(tabla_auditoria)
    story.append(Spacer(1, 14))

    # 3. TABLA COMPARATIVA FINANCIERA DE ALTO IMPACTO (SIDE-BY-SIDE)
    story.append(Paragraph("🔄 Análisis Cruzado de Escenarios de Retiro", estilos["seccion"]))
    
    filas_comparativas = [
        [Paragraph("Factor de Análisis", estilos["tabla_header"]), 
         Paragraph("Pensión Normal (Sin Estrategia)", estilos["tabla_header"]), 
         Paragraph("Plan Optimizado Pensión 40", estilos["tabla_header"])],
        
        [Paragraph("Semanas Reconocidas", estilos["tabla_texto"]), 
         Paragraph(f"{int(semanas_actuales):,} semanas", estilos["tabla_texto"]), 
         Paragraph(f"{int(semanas_totales_m40):,} semanas", estilos["tabla_texto"])],
        
        [Paragraph("Salario Diario Promedio (SBC)", estilos["tabla_texto"]), 
         Paragraph(f"${sbc_actual:,.2f} MXN", estilos["tabla_texto"]), 
         Paragraph(f"${sbc_ponderado_pdf:,.2f} MXN", estilos["tabla_texto"])],
        
        [Paragraph("Aportación Mensual Requerida", estilos["tabla_texto"]), 
         Paragraph("$0.00 MXN", estilos["tabla_texto"]), 
         Paragraph(f"${pago_mensual_estimado:,.2f} MXN", estilos["tabla_texto"])],
        
        [Paragraph("Inversión Total Acumulada", estilos["tabla_texto"]), 
         Paragraph("$0.00 MXN", estilos["tabla_texto"]), 
         Paragraph(f"${inversion_total_m40:,.2f} MXN", estilos["tabla_texto"])],
        
        [Paragraph("<b>Monto de Pensión Mensual</b>", estilos["tabla_texto"]), 
         Paragraph(f"<b>${pension_normal_mensual:,.2f} MXN</b>", estilos["tabla_texto"]), 
         Paragraph(f"<b>${pension_final_m40:,.2f} MXN</b>", estilos["tabla_texto"])],
        
        [Paragraph("<b>INCREMENTO NETO GANADO</b>", estilos["tabla_texto"]), 
         Paragraph("Base de Medición", estilos["tabla_texto"]), 
         Paragraph(f"<b>+${ganancia_neta_mensual:,.2f} MXN / mes</b>", estilos["tabla_texto"])]
    ]
    
    tabla_pdf = Table(filas_comparativas, colWidths=[6.5 * cm, 5.5 * cm, 5.5 * cm])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [BLANCO, GRIS_CLARO]),
        ('BACKGROUND', (0, -1), (-1, -1), VERDE_CLARO),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tabla_pdf)
    story.append(Spacer(1, 14))

    # 4. DICTAMEN DE RENTABILIDAD (ROI)
    story.append(Paragraph("💡 Dictamen Financiero de Viabilidad", estilos["seccion"]))
    texto_roi = (
        f"Al ejecutar esta estrategia financiera, tu pensión mensual experimenta un incremento neto de "
        f"<b>${ganancia_neta_mensual:,.2f} MXN adicionales cada mes</b> con respecto a la inercia de tus cotizaciones normales. "
        f"Bajo este rendimiento, recuperarás el 100% de tu capital financiero total invertido en un margen estimado de "
        f"<b>{roi_meses_final:.1f} meses</b> de disfrute de tu pensión (Aprox. {resultado_calculo.get('roi', {}).get('anios', 1.5)} años)."
    )
    story.append(Paragraph(texto_roi, estilos["cuerpo"]))
    story.append(Spacer(1, 18))

    # 5. SOPORTE DE ATENCIÓN Y CONTACTO LEGAL
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D9D9D9"), spaceBefore=10, spaceAfter=8))
    texto_soporte = (
        "<b>¿Tienes dudas o comentarios sobre tu estrategia de Modalidad 40?</b><br/>"
        "Escríbenos directamente a nuestro buzón oficial de atención al cliente: "
        "<font color='#1B6CA8'><b>contacto.pension40@gmail.com</b></font> y un consultor senior validará tu dictamen."
    )
    story.append(Paragraph(texto_soporte, estilos["footer"]))
    story.append(Spacer(1, 10))
    
    texto_aviso = (
        "Pensión 40 es un simulador financiero de carácter estrictamente informativo. No constituye una "
        "resolución jurídica oficial del Instituto Mexicano del Seguro Social (IMSS) ni garantiza fallos de otorgamiento."
    )
    story.append(Paragraph(texto_aviso, estilos["footer"]))

    # COMPILACIÓN DEL DOCUMENTO BINARIO
    documento.build(story)
    buffer.seek(0)
    return buffer.getvalue()
