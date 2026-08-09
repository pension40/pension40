import re
from datetime import datetime
from typing import Optional

# ... (Mantén tus clases de excepciones y funciones limpiar_texto, convertir_numero, convertir_fecha intactas)

# ============================================================
# MODIFICACIÓN 1: CORRECCIÓN DE LA REGEX DE SALARIO BASE (SBC)
# ============================================================
def _buscar_valor_monetario(texto: str) -> Optional[float]:
    """
    Detecta un valor monetario razonable.
    Modificado para aceptar números enteros sin punto decimal (ej. $450 o 563.9).
    """
    if not texto:
        return None
    
    # Expresión regular mejorada para capturar enteros o decimales opcionales
    patrones = [
        r"\$\s*([\d,]+(?:\.\d{1,2})?)",
        r"\b([\d,]+\.\d{2})\b",
        r"\b(\d+(?:\.\d{1,2})?)\b",
    ]
    for patron in patrones:
        encontrados = re.findall(patron, texto)
        for encontrado in encontrados:
            valor = convertir_numero(encontrado)
            if valor is None:
                continue
            if 1 <= valor <= 100000:
                return valor
    return None


# ============================================================
# MODIFICACIÓN 2: ELIMINACIÓN DE FILTRO DE DUPLICADOS DAÑINO
# ============================================================
def extraer_historial_laboral(ruta_pdf: str) -> list:
    """
    Extrae registros laborales de todas las tablas.
    Corregido: Ya no elimina duplicados legítimos por valores de celda idénticos.
    """
    tablas = extraer_tablas_pdf(ruta_pdf)
    registros = []
    
    for tabla_info in tablas:
        pagina = tabla_info["pagina"]
        filas = tabla_info["filas"]
        for fila in filas:
            registro = normalizar_registro_laboral(fila, pagina)
            if registro:
                registros.append(registro)
                
    # Ordenar de más reciente a más antiguo basándose en la fecha_fin
    registros.sort(
        key=lambda x: (x["fecha_fin"], x["fecha_inicio"]),
        reverse=True
    )
    return registros


# ============================================================
# MODIFICACIÓN 3: LÓGICA CRONOLÓGICA PARA LA PRIMERA COTIZACIÓN
# ============================================================
def extraer_primera_fecha_cotizacion_desde_historial(historial: list) -> Optional[datetime]:
    """
    Determina la verdadera primera fecha de cotización buscando el registro 
    laboral más antiguo en todo el historial extraído.
    """
    if not historial:
        return None
    
    # El historial está ordenado de más reciente a más antiguo,
    # por lo que el último elemento contiene los periodos más viejos.
    fechas_inicio = [reg["fecha_inicio"] for reg in historial]
    return min(fechas_inicio) if fechas_inicio else None


# ============================================================
# MODIFICACIÓN 4: FUNCIÓN PRINCIPAL ACTUALIZADA
# ============================================================
def analizar_pdf(ruta_pdf: str) -> dict:
    """
    Ejecuta todo el proceso de extracción utilizando la nueva lógica cronológica.
    """
    texto = extraer_texto_pdf(ruta_pdf)
    nombre = extraer_nombre(texto)
    nss = extraer_nss(texto)
    fecha_nacimiento = extraer_fecha_nacimiento(texto)
    
    # 1. Extraemos primero el historial completo de las tablas
    historial = extraer_historial_laboral(ruta_pdf)
    
    # 2. Encontramos la fecha más antigua real evaluando los datos del historial
    primera_fecha = extraer_primera_fecha_cotizacion_desde_historial(historial)
    
    # Si por alguna razón el historial falló, usamos la búsqueda por texto como respaldo técnico
    if primera_fecha is None:
        patrones_respaldo = [
            r"PRIMERA\s+FECHA.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"FECHA\s+DE\s+ALTA.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"FECHA\s+DE\s+INGRESO.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        for patron in patrones_respaldo:
            coincidencia = re.search(patron, texto, re.IGNORECASE)
            if coincidencia:
                fecha = convertir_fecha(coincidencia.group(1))
                if fecha:
                    primera_fecha = fecha
                    break

    # 3. Validación Definitiva de Ley 73
    ley_73 = validar_ley_73(primera_fecha)
    
    semanas = extraer_semanas_cotizadas(texto)
    validacion_semanas = validar_semanas(semanas)
    ultimas_250 = calcular_ultimas_250_semanas(historial)
    
    return {
        "nombre": nombre,
        "nss": nss,
        "fecha_nacimiento": fecha_nacimiento,
        "primera_fecha_cotizacion": primera_fecha,
        "ley_73": ley_73,
        "semanas_cotizadas": semanas,
        "validacion_semanas": validacion_semanas,
        "historial_laboral": historial,
        "ultimas_250_semanas": ultimas_250,
        "sbc_promedio": ultimas_250["sbc_promedio"]
    }
