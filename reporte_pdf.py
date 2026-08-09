# ============================================================
# PENSION 40
# reporte_pdf.py
# Generador del reporte financiero en PDF (ReportLab)
# ============================================================
#
# Este módulo NO calcula nada. Recibe el diccionario que
# devuelve calculador.calcular_escenario() y los datos del
# cliente, y construye un PDF ejecutivo listo para entregar
# al usuario cuando el reporte está desbloqueado
# (pago confirmado o código promocional válido).
#
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
    PageBreak,
)


# ============================================================
# PALETA CORPORATIVA (azul / confianza financiera)
# ============================================================

AZUL_OSCURO = colors.HexColor("#0B2545")
AZUL_PRINCIPAL = colors.HexColor("#134074")
AZUL_MEDIO = colors.HexColor("#1B6CA8")
AZUL_CLARO = colors.HexColor("#E8F1FA")
GRIS_TEXTO = colors.HexColor("#3B3B3B")
GRIS_CLARO = colors.HexColor("#F4F6F8")
VERDE_OK = colors.HexColor("#1E8A4C")
BLANCO = colors.white


# ============================================================
# ESTILOS DE TEXTO
# ============================================================

def _construir_estilos():

    base = getSampleStyleSheet()

    estilos = {}

    estilos["titulo"] = ParagraphStyle(
        "titulo",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    estilos["subtitulo"] = ParagraphStyle(
        "subtitulo",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=AZUL_MEDIO,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    estilos["seccion"] = ParagraphStyle(
        "seccion",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=AZUL_PRINCIPAL,
        spaceBefore=18,
        spaceAfter=8,
    )

    estilos["cuerpo"] = ParagraphStyle(
        "cuerpo",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=GRIS_TEXTO,
        leading=14,
    )

    estilos["nota"] = ParagraphStyle(
        "nota",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.HexColor("#6B6B6B"),
        leading=11,
    )

    estilos["dato_grande"] = ParagraphStyle(
        "dato_grande",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER,
    )

    estilos["dato_etiqueta"] = ParagraphStyle(
        "dato_etiqueta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=GRIS_TEXTO,
        alignment=TA_CENTER,
    )

    estilos["footer"] = ParagraphStyle(
        "footer",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#8A8A8A"),
        alignment=TA_CENTER,
    )

    return estilos


# ============================================================
# UTILIDADES DE FORMATO
# ============================================================

def _moneda(valor) -> str:

    try:
        return f"${float(valor):,.2f}"
    except (TypeError, ValueError):
        return "No disponible"


def _numero(valor) -> str:

    try:
        return f"{float(valor):,.0f}"
    except (TypeError, ValueError):
        return "No disponible"


# ============================================================
# BLOQUE: ENCABEZADO
# ============================================================

def _bloque_encabezado(estilos, nombre_cliente: str) -> list:

    elementos = []

    elementos.append(
        Paragraph("Pensión 40", estilos["titulo"])
    )

    elementos.append(
        Paragraph(
            "Reporte financiero · Proyección de pensión y Modalidad 40 (Ley 73 IMSS)",
            estilos["subtitulo"],
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=AZUL_MEDIO,
            spaceAfter=14,
        )
    )

    fecha_actual = datetime.now().strftime("%d/%m/%Y")

    datos_encabezado = Table(
        [
            [
                Paragraph(f"<b>Cliente:</b> {nombre_cliente or 'No especificado'}", estilos["cuerpo"]),
                Paragraph(f"<b>Fecha de emisión:</b> {fecha_actual}", estilos["cuerpo"]),
            ]
        ],
        colWidths=[9.5 * cm, 7.5 * cm],
    )

    datos_encabezado.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elementos.append(datos_encabezado)
    elementos.append(Spacer(1, 10))

    return elementos


# ============================================================
# BLOQUE: TARJETAS DE RESULTADO PRINCIPAL
# ============================================================

def _bloque_tarjetas_principales(estilos, pension: dict, roi: dict) -> list:

    elementos = []

    elementos.append(
        Paragraph("Resultado principal", estilos["seccion"])
    )

    pension_mensual = pension.get("pension_final_mensual")
    pension_anual = pension.get("pension_final_anual")
    meses_roi = roi.get("meses")

    valor_roi = (
        f"{meses_roi:.1f} meses" if meses_roi is not None else "No disponible"
    )

    celdas = [
        [
            Paragraph(_moneda(pension_mensual), estilos["dato_grande"]),
            Paragraph(_moneda(pension_anual), estilos["dato_grande"]),
            Paragraph(valor_roi, estilos["dato_grande"]),
        ],
        [
            Paragraph("Pensión mensual estimada", estilos["dato_etiqueta"]),
            Paragraph("Pensión anual estimada", estilos["dato_etiqueta"]),
            Paragraph("Recuperación de inversión", estilos["dato_etiqueta"]),
        ],
    ]

    tabla = Table(
        celdas,
        colWidths=[5.6 * cm, 5.6 * cm, 5.6 * cm],
        rowHeights=[1.1 * cm, 0.7 * cm],
    )

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
                ("BOX", (0, 0), (0, -1), 0.75, AZUL_MEDIO),
                ("BOX", (1, 0), (1, -1), 0.75, AZUL_MEDIO),
                ("BOX", (2, 0), (2, -1), 0.75, AZUL_MEDIO),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    elementos.append(tabla)
    elementos.append(Spacer(1, 14))

    return elementos


# ============================================================
# BLOQUE: DATOS DEL CÁLCULO
# ============================================================

def _bloque_datos_generales(estilos, parametros: dict, pension: dict) -> list:

    elementos = []

    elementos.append(
        Paragraph("Datos utilizados en el cálculo", estilos["seccion"])
    )

    filas = [
        ["Concepto", "Valor"],
        ["SBC promedio (últimas 250 semanas)", _moneda(parametros.get("sbc_promedio"))],
        ["Semanas cotizadas", _numero(parametros.get("semanas"))],
        ["Edad considerada", str(parametros.get("edad", "No disponible"))],
        ["UMA utilizada", _moneda(parametros.get("uma"))],
        ["Grupo salarial", str(pension.get("grupo_salarial", "No disponible"))],
        ["Cuantía básica", f"{pension.get('cuantia_basica', 0) * 100:.2f}%"],
        ["Porcentaje por edad de retiro", f"{pension.get('porcentaje_edad', 0):.0f}%"],
        ["Factor de incremento (Fox)", f"{pension.get('factor_fox', {}).get('factor', 1):.2f}"],
        [
            "Asignación familiar",
            f"{pension.get('asignacion_familiar', {}).get('porcentaje', 0) * 100:.0f}%",
        ],
    ]

    tabla = Table(filas, colWidths=[10 * cm, 6.7 * cm])

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRINCIPAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elementos.append(tabla)
    elementos.append(Spacer(1, 6))

    return elementos


# ============================================================
# BLOQUE: MODALIDAD 40
# ============================================================

def _bloque_modalidad_40(estilos, parametros: dict, m40: dict) -> list:

    elementos = []

    elementos.append(
        Paragraph("Estrategia de Modalidad 40", estilos["seccion"])
    )

    salario = m40.get("salario", {})
    inversion = m40.get("inversion", {})

    filas = [
        ["Concepto", "Valor"],
        ["Salario diario aplicado", _moneda(salario.get("sbc_aplicado"))],
        ["Duración de la estrategia", f"{parametros.get('meses_modalidad_40', 'No disponible')} meses"],
        ["Inversión total estimada", _moneda(inversion.get("inversion_total"))],
    ]

    tabla = Table(filas, colWidths=[10 * cm, 6.7 * cm])

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL_MEDIO),
                ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elementos.append(tabla)
    elementos.append(Spacer(1, 6))

    # --------------------------------------------------------
    # Tabla mensual (primeros 12 meses o los que existan)
    # --------------------------------------------------------

    tabla_mensual = inversion.get("tabla_mensual", [])

    if tabla_mensual:

        elementos.append(Spacer(1, 10))

        elementos.append(
            Paragraph(
                "Proyección de inversión mensual (primeros 12 meses)",
                estilos["cuerpo"],
            )
        )

        elementos.append(Spacer(1, 6))

        encabezado = ["Mes", "Año", "Tasa", "Costo mensual", "Acumulado"]
        filas_detalle = [encabezado]

        for fila in tabla_mensual[:12]:

            filas_detalle.append(
                [
                    str(fila.get("mes", "")),
                    str(fila.get("anio", "")),
                    f"{fila.get('tasa', 0):.3f}%",
                    _moneda(fila.get("costo_mensual")),
                    _moneda(fila.get("inversion_acumulada")),
                ]
            )

        tabla_detalle = Table(
            filas_detalle,
            colWidths=[1.8 * cm, 2.2 * cm, 2.5 * cm, 4.6 * cm, 5.6 * cm],
        )

        tabla_detalle.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
                    ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (3, 1), (4, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        elementos.append(tabla_detalle)

        if len(tabla_mensual) > 12:

            elementos.append(Spacer(1, 4))

            elementos.append(
                Paragraph(
                    f"Se muestran los primeros 12 de {len(tabla_mensual)} meses "
                    "de la estrategia completa.",
                    estilos["nota"],
                )
            )

    return elementos


# ============================================================
# BLOQUE: CONCLUSIÓN / ROI
# ============================================================

def _bloque_conclusion(estilos, roi: dict) -> list:

    elementos = []

    elementos.append(
        Paragraph("Retorno de inversión (ROI)", estilos["seccion"])
    )

    mensaje = roi.get("mensaje", "")
    anios = roi.get("anios")

    texto = mensaje

    if anios is not None:
        texto += f" Aproximadamente {anios:.2f} años."

    elementos.append(
        Paragraph(texto, estilos["cuerpo"])
    )

    elementos.append(Spacer(1, 10))

    return elementos


# ============================================================
# BLOQUE: AVISO LEGAL
# ============================================================

def _bloque_aviso_legal(estilos) -> list:

    elementos = []

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=0.75,
            color=colors.HexColor("#D9D9D9"),
            spaceBefore=16,
            spaceAfter=8,
        )
    )

    elementos.append(
        Paragraph(
            "Este reporte es una estimación financiera generada por el simulador "
            "Pensión 40 con base en los datos proporcionados por el usuario y la "
            "normativa vigente del régimen de Ley 73 del IMSS. No constituye una "
            "resolución oficial del Instituto Mexicano del Seguro Social ni "
            "garantiza el monto final de la pensión, el cual depende de la "
            "resolución definitiva del IMSS al momento del trámite.",
            estilos["footer"],
        )
    )

    return elementos


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def generar_reporte_pdf(
    nombre_cliente: str,
    resultado_calculo: dict,
) -> bytes:
    """
    Construye el PDF ejecutivo del reporte financiero.

    Parámetros
    ----------
    nombre_cliente:
        Nombre completo del cliente, para el encabezado.

    resultado_calculo:
        Diccionario devuelto por
        calculador.calcular_escenario().

    Retorna
    -------
    bytes:
        Contenido binario del PDF, listo para
        st.download_button o para guardar en disco.
    """

    if not resultado_calculo:
        raise ValueError(
            "No fue posible generar el reporte: falta el resultado del cálculo."
        )

    buffer = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Reporte Pensión 40",
    )

    estilos = _construir_estilos()

    parametros = resultado_calculo.get("parametros", {})
    pension = resultado_calculo.get("pension", {})
    m40 = resultado_calculo.get("modalidad_40", {})
    roi = resultado_calculo.get("roi", {})

    story = []

    story += _bloque_encabezado(estilos, nombre_cliente)
    story += _bloque_tarjetas_principales(estilos, pension, roi)
    story += _bloque_datos_generales(estilos, parametros, pension)
    story += _bloque_modalidad_40(estilos, parametros, m40)
    story += _bloque_conclusion(estilos, roi)
    story += _bloque_aviso_legal(estilos)

    documento.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# PRUEBA RÁPIDA DEL GENERADOR
# ============================================================

if __name__ == "__main__":

    from calculador import calcular_escenario

    resultado_prueba = calcular_escenario(
        sbc_promedio=850.50,
        semanas=1200,
        edad=60,
        uma=113.14,
        tipo_asignacion="esposa",
        meses_modalidad_40=58,
    )

    pdf_bytes = generar_reporte_pdf(
        nombre_cliente="Juan Pérez López",
        resultado_calculo=resultado_prueba,
    )

    with open("reporte_prueba.pdf", "wb") as archivo:
        archivo.write(pdf_bytes)

    print(f"PDF generado: {len(pdf_bytes):,} bytes")
