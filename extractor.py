# ============================================================
# PENSION 40
# Módulo: extractor.py - Bloque 1 de 4
# ============================================================

import re
from datetime import datetime
from typing import Optional

class ExtractorPensionError(Exception):
    """Error general del extractor."""
    pass

class Ley97Error(ExtractorPensionError):
    """El asegurado pertenece a Ley 97."""
    pass

class SemanasInsuficientesError(ExtractorPensionError):
    """No se alcanzan las semanas mínimas."""
    pass

class PDFInvalidoError(ExtractorPensionError):
    """El PDF no pudo ser leído correctamente."""
    pass

def limpiar_texto(texto: Optional[str]) -> str:
    """Limpia espacios duplicados y saltos de línea."""
    if texto is None:
        return ""
    texto = str(texto)
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def convertir_numero(valor) -> Optional[float]:
    """Convierte cadenas monetarias o numéricas a flotante."""
    if valor is None:
        return None
    texto = limpiar_texto(str(valor))
    texto = texto.replace("$", "").replace("MXN", "").replace(" ", "")
    if "," in texto and "." in texto:
        texto = texto.replace(",", "")
    elif "," in texto and "." not in texto:
        partes = texto.split(",")
        if len(partes) == 2 and len(partes[1]) <= 2:
            texto = ".".join(partes)
        else:
            texto = texto.replace(",", "")
    try:
        return float(texto)
    except (ValueError, TypeError):
        return None

def convertir_fecha(valor) -> Optional[datetime]:
    """Prueba múltiples formatos para convertir texto a datetime."""
    if valor is None:
        return None
    texto = limpiar_texto(str(valor))
    formatos = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]
    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None
# ============================================================
# PENSION 40
# Módulo: extractor.py - Bloque 2 de 4
# ============================================================

def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae todo el texto plano del PDF usando pdfplumber."""
    import pdfplumber
    textos = []
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    textos.append(texto)
    except Exception as error:
        raise PDFInvalidoError(f"No fue posible abrir el PDF: {error}")
    
    texto_final = "\n".join(textos)
    if not texto_final.strip():
        raise PDFInvalidoError("El PDF no contiene texto legible.")
    return texto_final

def extraer_nombre(texto: str) -> Optional[str]:
    """Busca el nombre completo del asegurado en el texto plano."""
    patrones = [
        r"NOMBRE\s*[:\-]?\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,})",
        r"ASEGURADO\s*[:\-]?\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,})",
        r"([A-ZÁÉÍÓÚÑÜ\s]{5,})\nNSS\s*:"
    ]
    for patron in patrones:
        coincidencia = re.search(patron, texto, re.IGNORECASE)
        if coincidencia:
            return coincidencia.group(1).strip()
    return "No detectado"

def extraer_nss(texto: str) -> Optional[str]:
    """Busca y extrae el NSS de 11 dígitos válido."""
    coincidencias = re.findall(r"\b\d{11}\b", texto)
    return coincidencias[0] if coincidencias else "No detectado"

def extraer_semanas_cotizadas(texto: str) -> Optional[float]:
    """Extrae el gran total de semanas cotizadas del documento."""
    patrones = [
        r"Total de semanas cotizadas\s*(\d+)",
        r"Número total de semanas cotizadas\s*:\s*(\d+)",
        r"SEMANAS\s+COTIZADAS\s*[:\-]?\s*([\d,]+)"
    ]
    for patron in patrones:
        coincidencia = re.search(patron, texto, re.IGNORECASE)
        if coincidencia:
            return convertir_numero(coincidencia.group(1))
    return None
# ============================================================
# PENSION 40
# Módulo: extractor.py - Bloque 3 de 4
# ============================================================

def extraer_historial_laboral_por_texto(texto: str) -> list:
    """
    Parsea secuencialmente las líneas de movimientos afiliatorios del IMSS.
    Empareja altas y bajas cronológicamente para generar periodos y días cotizados.
    """
    lineas = texto.split("\n")
    movimientos = []
    
    # Captura movimientos del IMSS aceptando decimales opcionales en el salario diario
    patron_movimiento = r"(REINGRESO|BAJA|MODIFICACION\s+DE\s+SALARIO|ALTA)\s+(\d{2}/\d{2}/\d{4})\s+\$\s*([\d,]+\.?\d*)"
    
    for linea in lineas:
        match = re.search(patron_movimiento, linea, re.IGNORECASE)
        if match:
            tipo, fecha_str, sbc_str = match.groups()
            movimientos.append({
                "tipo": tipo.upper(),
                "fecha": convertir_fecha(fecha_str),
                "sbc": convertir_numero(sbc_str)
            })

    # Asegura orden cronológico de lo más reciente a lo más antiguo
    movimientos.sort(key=lambda x: x["fecha"], reverse=True)
    
    historial_periodos = []
    fecha_baja_actual = None
    sbc_actual = None

    for mov in movimientos:
        if mov["tipo"] == "BAJA":
            fecha_baja_actual = mov["fecha"]
            sbc_actual = mov["sbc"]
        elif mov["tipo"] in ["REINGRESO", "ALTA"]:
            if fecha_baja_actual is not None:
                dias = (fecha_baja_actual - mov["fecha"]).days + 1
                historial_periodos.append({
                    "fecha_inicio": mov["fecha"],
                    "fecha_fin": fecha_baja_actual,
                    "dias": max(1, dias),
                    "sbc": sbc_actual if sbc_actual else mov["sbc"]
                })
            else:
                # Caso de asegurado con estatus Vigente
                dias = (datetime.now() - mov["fecha"]).days + 1
                historial_periodos.append({
                    "fecha_inicio": mov["fecha"],
                    "fecha_fin": datetime.now(),
                    "dias": max(1, dias),
                    "sbc": mov["sbc"]
                })
            fecha_baja_actual = None
        elif mov["tipo"] == "MODIFICACION DE SALARIO":
            if fecha_baja_actual is not None:
                dias = (fecha_baja_actual - mov["fecha"]).days + 1
                historial_periodos.append({
                    "fecha_inicio": mov["fecha"],
                    "fecha_fin": fecha_baja_actual,
                    "dias": max(1, dias),
                    "sbc": sbc_actual if sbc_actual else mov["sbc"]
                })
            fecha_baja_actual = mov["fecha"]
            sbc_actual = mov["sbc"]

    return historial_periodos
# ============================================================
# PENSION 40
# Módulo: extractor.py - Bloque 4 de 4
# ============================================================

def validar_ley_73(primera_fecha: Optional[datetime]) -> bool:
    """Verifica si la primera fecha de cotización pertenece a Ley 73 o Ley 97."""
    if primera_fecha is None:
        raise ExtractorPensionError("No fue posible determinar la primera fecha de cotización.")
    fecha_limite = datetime(1997, 6, 30)
    if primera_fecha > fecha_limite:
        raise Ley97Error(f"La primera cotización es del {primera_fecha.strftime('%d/%m/%Y')}. Corresponde al régimen de Ley 97.")
    return True

def validar_semanas(semanas: Optional[float]) -> dict:
    """Evalúa si el asegurado cuenta con las 500 semanas mínimas para pensionarse."""
    if semanas is None:
        return {"validas": False, "semanas": None, "faltantes": None, "mensaje": "No se determinaron las semanas."}
    faltantes = max(0, 500 - semanas)
    return {
        "validas": semanas >= 500,
        "semanas": semanas,
        "faltantes": faltantes,
        "mensaje": "Cumple con el mínimo de 500 semanas." if semanas >= 500 else f"Faltan {faltantes:g} semanas para el mínimo."
    }

def calcular_ultimas_250_semanas(registros: list) -> dict:
    """Acumula exactamente 1,750 días cotizados del historial para promediar el SBC."""
    objetivo_dias = 250 * 7
    dias_acumulados = 0
    suma_sbc_dias = 0.0
    registros_utilizados = []

    for registro in registros:
        if dias_acumulados >= objetivo_dias:
            break
        dias_disponibles = int(registro["dias"])
        if dias_disponibles <= 0:
            continue
        
        dias_necesarios = objetivo_dias - dias_acumulados
        dias_utilizados = min(dias_disponibles, dias_necesarios)
        
        suma_sbc_dias += float(registro["sbc"]) * dias_utilizados
        dias_acumulados += dias_utilizados
        
        registros_utilizados.append({
            **registro,
            "dias_utilizados": dias_utilizados
        })

    if dias_acumulados == 0:
        raise ExtractorPensionError("No se encontraron días cotizados para calcular las últimas 250 semanas.")
        
    promedio = suma_sbc_dias / dias_acumulados
    return {
        "dias_objetivo": objetivo_dias,
        "dias_acumulados": dias_acumulados,
        "semanas_equivalentes": dias_acumulados / 7,
        "sbc_promedio": round(promedio, 2),
        "registros_utilizados": registros_utilizados,
        "completo": dias_acumulados >= objetivo_dias
    }

def analizar_pdf(ruta_pdf: str) -> dict:
    """Función de extracción orquestadora principal de datos."""
    texto = extraer_texto_pdf(ruta_pdf)
    nombre = extraer_nombre(texto)
    nss = extraer_nss(texto)
    semanas = extraer_semanas_cotizadas(texto)
    
    historial = extraer_historial_laboral_por_texto(texto)
    
    # Determina la fecha más antigua real evaluando cronológicamente el historial
    primera_fecha = min([reg["fecha_inicio"] for reg in historial]) if historial else None
        
    validar_ley_73(primera_fecha)
    validacion_semanas = validar_semanas(semanas)
    ultimas_250 = calcular_ultimas_250_semanas(historial)
    
    # El retorno incluye la llave "ley" con "Ley 73" para compatibilidad exacta con tu app.py
    return {
        "nombre": nombre,
        "nss": nss,
        "primera_fecha_cotizacion": primera_fecha,
        "ley": "Ley 73",
        "semanas_cotizadas": semanas,
        "validacion_semanas": validacion_semanas,
        "historial_laboral": historial,
        "ultimas_250_semanas": ultimas_250,
        "sbc_promedio": ultimas_250["sbc_promedio"]
    }

def analizar_pdf_streamlit(archivo_subido) -> dict:
    """Manejador seguro de archivos temporales para st.file_uploader."""
    import os
    import tempfile
    if archivo_subido is None:
        raise ValueError("No se recibió ningún archivo PDF.")
    if not archivo_subido.name.lower().endswith(".pdf"):
        raise PDFInvalidoError("El archivo debe ser un PDF.")
    
    archivo_temporal = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temporal:
            temporal.write(archivo_subido.getbuffer())
            archivo_temporal = temporal.name
        resultado = analizar_pdf(archivo_temporal)
        return resultado
    finally:
        if archivo_temporal and os.path.exists(archivo_temporal):
            try:
                os.remove(archivo_temporal)
            except OSError:
                pass
