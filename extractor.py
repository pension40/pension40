# ============================================================
# PENSION 40
# extractor.py
# ============================================================
#
# Módulo para extracción y análisis del PDF de semanas cotizadas
# del IMSS.
#
# Funciones principales:
#   - Leer PDF con pdfplumber
#   - Detectar primera fecha de cotización
#   - Determinar Ley 73 / Ley 97
#   - Extraer semanas cotizadas
#   - Extraer historial laboral
#   - Recorrer el historial de lo más reciente a lo más antiguo
#   - Acumular exactamente 1,750 días cuando sea posible
#   - Calcular SBC promedio de las últimas 250 semanas
#
# IMPORTANTE:
# El formato del PDF del IMSS puede cambiar. Este módulo está
# preparado para tolerar diferentes posiciones de columnas,
# pero deberá probarse con el PDF real.
# ============================================================

import re
from datetime import datetime
from typing import Optional

import pdfplumber


# ============================================================
# EXCEPCIONES
# ============================================================

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


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def limpiar_texto(texto: Optional[str]) -> str:
    """
    Limpia espacios y saltos de línea.
    """

    if texto is None:
        return ""

    texto = str(texto)

    texto = texto.replace("\xa0", " ")

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def convertir_numero(valor) -> Optional[float]:
    """
    Convierte textos como:

        629.59
        $629.59
        1,234.56
        629,59

    a número.
    """

    if valor is None:
        return None

    texto = limpiar_texto(str(valor))

    texto = (
        texto
        .replace("$", "")
        .replace("MXN", "")
        .replace(" ", "")
    )

    # Caso común mexicano:
    # 1,234.56
    if "," in texto and "." in texto:

        texto = texto.replace(",", "")

    # Caso 629,59
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
    """
    Intenta convertir diferentes formatos de fecha.
    """

    if valor is None:
        return None

    texto = limpiar_texto(str(valor))

    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]

    for formato in formatos:

        try:
            return datetime.strptime(
                texto,
                formato
            )

        except ValueError:
            continue

    return None


# ============================================================
# EXTRACCIÓN DE TEXTO
# ============================================================

def extraer_texto_pdf(ruta_pdf: str) -> str:
    """
    Extrae todo el texto disponible del PDF.
    """

    textos = []

    try:

        with pdfplumber.open(ruta_pdf) as pdf:

            for pagina in pdf.pages:

                texto = pagina.extract_text()

                if texto:
                    textos.append(texto)

    except Exception as error:

        raise PDFInvalidoError(
            f"No fue posible abrir el PDF: {error}"
        )

    texto_final = "\n".join(textos)

    if not texto_final.strip():

        raise PDFInvalidoError(
            "El PDF no contiene texto legible."
        )

    return texto_final


# ============================================================
# NOMBRE
# ============================================================

def extraer_nombre(texto: str) -> Optional[str]:
    """
    Busca el nombre del asegurado.

    Se contemplan diferentes etiquetas que pueden aparecer
    en documentos del IMSS.
    """

    patrones = [
        r"NOMBRE\s*[:\-]?\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,})",
        r"ASEGURADO\s*[:\-]?\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,})",
    ]

    for patron in patrones:

        coincidencia = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if coincidencia:

            nombre = limpiar_texto(
                coincidencia.group(1)
            )

            return nombre.strip()

    return None


# ============================================================
# NSS
# ============================================================

def extraer_nss(texto: str) -> Optional[str]:
    """
    Busca un NSS de 11 dígitos.
    """

    patrones = [
        r"NSS\s*[:\-]?\s*(\d{11})",
        r"N[ÚU]MERO\s+DE\s+SEGURIDAD\s+SOCIAL\s*[:\-]?\s*(\d{11})",
    ]

    for patron in patrones:

        coincidencia = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if coincidencia:

            return coincidencia.group(1)

    # Búsqueda secundaria de 11 dígitos
    candidatos = re.findall(
        r"\b\d{11}\b",
        texto
    )

    if candidatos:

        return candidatos[0]

    return None


# ============================================================
# FECHA DE NACIMIENTO
# ============================================================

def extraer_fecha_nacimiento(
    texto: str
) -> Optional[datetime]:
    """
    Busca fecha de nacimiento.
    """

    patrones = [
        r"FECHA\s+DE\s+NACIMIENTO\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"NACIMIENTO\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]

    for patron in patrones:

        coincidencia = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if coincidencia:

            fecha = convertir_fecha(
                coincidencia.group(1)
            )

            if fecha:
                return fecha

    return None


# ============================================================
# PRIMERA FECHA DE COTIZACIÓN
# ============================================================

def extraer_primera_fecha_cotizacion(
    texto: str
) -> Optional[datetime]:
    """
    Busca fechas relacionadas con el primer registro laboral.

    La lógica definitiva deberá contrastarse con las tablas
    del historial laboral.
    """

    patrones = [
        r"PRIMERA\s+FECHA.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"FECHA\s+DE\s+ALTA.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"FECHA\s+DE\s+INGRESO.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]

    for patron in patrones:

        coincidencia = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if coincidencia:

            fecha = convertir_fecha(
                coincidencia.group(1)
            )

            if fecha:
                return fecha

    return None


# ============================================================
# LEY 73
# ============================================================

def validar_ley_73(
    primera_fecha_cotizacion: Optional[datetime]
) -> bool:
    """
    Determina si el asegurado cumple con el criterio temporal
    para régimen de transición.

    Fecha límite:
        30 de junio de 1997.

    Si la primera cotización es posterior a esa fecha,
    se considera Ley 97 para efectos del sistema.
    """

    if primera_fecha_cotizacion is None:

        raise ExtractorPensionError(
            "No fue posible determinar la primera fecha "
            "de cotización."
        )

    fecha_limite = datetime(
        1997,
        6,
        30
    )

    if primera_fecha_cotizacion > fecha_limite:

        raise Ley97Error(
            "La primera cotización es posterior al "
            "30 de junio de 1997. El asegurado corresponde "
            "al régimen de Ley 97."
        )

    return True


# ============================================================
# SEMANAS COTIZADAS
# ============================================================

def extraer_semanas_cotizadas(
    texto: str
) -> Optional[float]:
    """
    Busca el total de semanas cotizadas.
    """

    patrones = [
        r"SEMANAS\s+COTIZADAS\s*[:\-]?\s*([\d,]+(?:\.\d+)?)",
        r"TOTAL\s+DE\s+SEMANAS\s*[:\-]?\s*([\d,]+(?:\.\d+)?)",
        r"SEMANAS\s*[:\-]?\s*([\d,]+(?:\.\d+)?)",
    ]

    for patron in patrones:

        coincidencia = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if coincidencia:

            valor = convertir_numero(
                coincidencia.group(1)
            )

            if valor is not None:
                return valor

    return None


# ============================================================
# VALIDAR SEMANAS
# ============================================================

def validar_semanas(
    semanas: Optional[float]
) -> dict:
    """
    Comprueba el mínimo de 500 semanas.

    No bloquea el análisis cuando son menores a 500:
    devuelve información para que la interfaz pueda explicar
    cuántas semanas faltan.
    """

    if semanas is None:

        return {
            "validas": False,
            "semanas": None,
            "faltantes": None,
            "mensaje": (
                "No fue posible determinar las semanas "
                "cotizadas."
            )
        }

    faltantes = max(
        0,
        500 - semanas
    )

    if semanas >= 500:

        return {
            "validas": True,
            "semanas": semanas,
            "faltantes": 0,
            "mensaje": (
                "Cumple con el mínimo de 500 semanas."
            )
        }

    return {
        "validas": False,
        "semanas": semanas,
        "faltantes": faltantes,
        "mensaje": (
            f"Faltan {faltantes:g} semanas para alcanzar "
            "las 500 semanas mínimas."
        )
    }


# ============================================================
# EXTRACCIÓN DE TABLAS
# ============================================================

def extraer_tablas_pdf(
    ruta_pdf: str
) -> list:
    """
    Extrae todas las tablas detectables mediante pdfplumber.

    Retorna una lista de tablas.
    """

    tablas = []

    try:

        with pdfplumber.open(ruta_pdf) as pdf:

            for numero_pagina, pagina in enumerate(
                pdf.pages,
                start=1
            ):

                try:

                    tablas_pagina = pagina.extract_tables()

                except Exception:

                    tablas_pagina = []

                for tabla in tablas_pagina:

                    if tabla:

                        tablas.append(
                            {
                                "pagina": numero_pagina,
                                "filas": tabla
                            }
                        )

    except Exception as error:

        raise PDFInvalidoError(
            f"No fue posible extraer las tablas: {error}"
        )

    return tablas


# ============================================================
# DETECCIÓN DE REGISTROS LABORALES
# ============================================================

def _fila_contiene_fecha(fila) -> bool:
    """
    Determina si una fila contiene al menos una fecha.
    """

    if not fila:
        return False

    texto = " ".join(
        limpiar_texto(celda)
        for celda in fila
        if celda is not None
    )

    patron_fecha = (
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    )

    return bool(
        re.search(
            patron_fecha,
            texto
        )
    )


def _extraer_fechas_de_fila(fila) -> list:
    """
    Extrae todas las fechas encontradas en una fila.
    """

    texto = " ".join(
        limpiar_texto(celda)
        for celda in fila
        if celda is not None
    )

    encontrados = re.findall(
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        texto
    )

    fechas = []

    for fecha_texto in encontrados:

        fecha = convertir_fecha(
            fecha_texto
        )

        if fecha:
            fechas.append(fecha)

    return fechas


def _buscar_numero_dias(fila) -> Optional[int]:
    """
    Intenta localizar días cotizados dentro de una fila.

    Se utilizan primero etiquetas explícitas y después
    candidatos numéricos.
    """

    if not fila:
        return None

    celdas = [
        limpiar_texto(celda)
        for celda in fila
        if celda is not None
    ]

    # --------------------------------------------------------
    # Buscar una celda que claramente indique días
    # --------------------------------------------------------

    for indice, celda in enumerate(celdas):

        if re.search(
            r"D[IÍ]AS",
            celda,
            re.IGNORECASE
        ):

            numeros = re.findall(
                r"\d+",
                celda
            )

            if numeros:

                try:
                    return int(numeros[-1])
                except ValueError:
                    pass

            # Revisar celda siguiente
            if indice + 1 < len(celdas):

                numeros = re.findall(
                    r"\d+",
                    celdas[indice + 1]
                )

                if numeros:

                    try:
                        return int(numeros[-1])
                    except ValueError:
                        pass

    return None


def _buscar_sbc(fila) -> Optional[float]:
    """
    Intenta encontrar el Salario Base de Cotización (SBC)
    en una fila.

    Se buscan etiquetas SBC / SALARIO BASE y posteriormente
    valores monetarios.
    """

    if not fila:
        return None

    celdas = [
        limpiar_texto(celda)
        for celda in fila
        if celda is not None
    ]

    # --------------------------------------------------------
    # Buscar etiqueta explícita
    # --------------------------------------------------------

    for indice, celda in enumerate(celdas):

        if re.search(
            r"\bSBC\b|SALARIO\s+BASE",
            celda,
            re.IGNORECASE
        ):

            # Revisar números dentro de la misma celda
            valor = _buscar_valor_monetario(celda)

            if valor is not None:
                return valor

            # Revisar siguientes celdas
            for siguiente in range(
                indice + 1,
                min(indice + 3, len(celdas))
            ):

                valor = _buscar_valor_monetario(
                    celdas[siguiente]
                )

                if valor is not None:
                    return valor

    # --------------------------------------------------------
    # Segunda estrategia:
    # Buscar valores con formato monetario.
    # --------------------------------------------------------

    candidatos = []

    for celda in celdas:

        valor = _buscar_valor_monetario(celda)

        if valor is not None:
            candidatos.append(valor)

    if candidatos:

        # De momento tomamos el último candidato.
        # Se ajustará con el formato real del PDF.
        return candidatos[-1]

    return None


def _buscar_valor_monetario(
    texto: str
) -> Optional[float]:
    """
    Detecta un valor monetario razonable.
    """

    if not texto:
        return None

    patrones = [
        r"\$\s*([\d,]+\.\d{2})",
        r"\b([\d,]+\.\d{2})\b",
        r"\b(\d+\.\d{1,2})\b",
    ]

    for patron in patrones:

        encontrados = re.findall(
            patron,
            texto
        )

        for encontrado in encontrados:

            valor = convertir_numero(
                encontrado
            )

            if valor is None:
                continue

            # Evitar valores absurdos.
            if 1 <= valor <= 100000:
                return valor

    return None


# ============================================================
# NORMALIZACIÓN DEL HISTORIAL
# ============================================================

def normalizar_registro_laboral(
    fila,
    pagina: int
) -> Optional[dict]:
    """
    Convierte una fila de tabla en un registro laboral.

    Esta función será afinada una vez que conozcamos
    exactamente el formato del PDF.
    """

    if not fila:
        return None

    if not _fila_contiene_fecha(fila):
        return None

    fechas = _extraer_fechas_de_fila(fila)

    if not fechas:
        return None

    fecha_inicio = min(fechas)

    fecha_fin = max(fechas)

    sbc = _buscar_sbc(fila)

    dias = _buscar_numero_dias(fila)

    if dias is None:

        # Si existen dos fechas, calculamos días aproximados
        # como respaldo.
        if fecha_fin >= fecha_inicio:

            dias = (
                fecha_fin - fecha_inicio
            ).days + 1

    if sbc is None or dias is None:

        return None

    return {
        "pagina": pagina,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias": int(dias),
        "sbc": float(sbc)
    }


# ============================================================
# HISTORIAL LABORAL COMPLETO
# ============================================================

def extraer_historial_laboral(
    ruta_pdf: str
) -> list:
    """
    Extrae registros laborales de todas las tablas.

    El resultado se ordena de lo más reciente a lo más antiguo.
    """

    tablas = extraer_tablas_pdf(
        ruta_pdf
    )

    registros = []

    for tabla_info in tablas:

        pagina = tabla_info["pagina"]

        filas = tabla_info["filas"]

        for fila in filas:

            registro = normalizar_registro_laboral(
                fila,
                pagina
            )

            if registro:

                registros.append(
                    registro
                )

    # --------------------------------------------------------
    # Eliminar duplicados aproximados
    # --------------------------------------------------------

    unicos = {}

    for registro in registros:

        clave = (
            registro["fecha_inicio"],
            registro["fecha_fin"],
            registro["dias"],
            round(
                registro["sbc"],
                2
            )
        )

        unicos[clave] = registro

    registros = list(
        unicos.values()
    )

    # --------------------------------------------------------
    # Ordenar de más reciente a más antiguo
    # --------------------------------------------------------

    registros.sort(
        key=lambda x: (
            x["fecha_fin"],
            x["fecha_inicio"]
        ),
        reverse=True
    )

    return registros


# ============================================================
# ÚLTIMAS 250 SEMANAS
# ============================================================

def calcular_ultimas_250_semanas(
    registros: list
) -> dict:
    """
    Recorre el historial desde lo más reciente hacia atrás
    y acumula exactamente 1,750 días cuando es posible.

    Se calcula un promedio ponderado por días.

    IMPORTANTE:
    Si el último registro necesario contiene más días de los
    requeridos, solamente se utiliza la parte necesaria.
    """

    objetivo_dias = 250 * 7

    dias_acumulados = 0

    suma_sbc_dias = 0.0

    registros_utilizados = []

    for registro in registros:

        if dias_acumulados >= objetivo_dias:
            break

        dias_disponibles = int(
            registro["dias"]
        )

        if dias_disponibles <= 0:
            continue

        dias_necesarios = (
            objetivo_dias - dias_acumulados
        )

        dias_utilizados = min(
            dias_disponibles,
            dias_necesarios
        )

        sbc = float(
            registro["sbc"]
        )

        suma_sbc_dias += (
            sbc * dias_utilizados
        )

        dias_acumulados += (
            dias_utilizados
        )

        registros_utilizados.append(
            {
                **registro,
                "dias_utilizados":
                    dias_utilizados
            }
        )

    if dias_acumulados == 0:

        raise ExtractorPensionError(
            "No se encontraron días cotizados "
            "para calcular las últimas 250 semanas."
        )

    promedio = (
        suma_sbc_dias /
        dias_acumulados
    )

    return {
        "dias_objetivo": objetivo_dias,
        "dias_acumulados": dias_acumulados,
        "semanas_equivalentes":
            dias_acumulados / 7,
        "sbc_promedio":
            round(promedio, 2),
        "registros_utilizados":
            registros_utilizados,
        "completo":
            dias_acumulados >= objetivo_dias
    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def analizar_pdf(
    ruta_pdf: str
) -> dict:
    """
    Ejecuta todo el proceso de extracción.

    Retorna un diccionario con los datos principales.
    """

    texto = extraer_texto_pdf(
        ruta_pdf
    )

    nombre = extraer_nombre(
        texto
    )

    nss = extraer_nss(
        texto
    )

    fecha_nacimiento = (
        extraer_fecha_nacimiento(
            texto
        )
    )

    primera_fecha = (
        extraer_primera_fecha_cotizacion(
            texto
        )
    )

    # --------------------------------------------------------
    # Validación Ley 73
    # --------------------------------------------------------

    ley_73 = validar_ley_73(
        primera_fecha
    )

    semanas = extraer_semanas_cotizadas(
        texto
    )

    validacion_semanas = validar_semanas(
        semanas
    )

    # --------------------------------------------------------
    # Historial laboral
    # --------------------------------------------------------

    historial = extraer_historial_laboral(
        ruta_pdf
    )

    ultimas_250 = calcular_ultimas_250_semanas(
        historial
    )

    return {
        "nombre": nombre,
        "nss": nss,
        "fecha_nacimiento":
            fecha_nacimiento,
        "primera_fecha_cotizacion":
            primera_fecha,
        "ley_73": ley_73,
        "semanas_cotizadas": semanas,
        "validacion_semanas":
            validacion_semanas,
        "historial_laboral":
            historial,
        "ultimas_250_semanas":
            ultimas_250,
        "sbc_promedio":
            ultimas_250["sbc_promedio"]
    }


# ============================================================
# FUNCIÓN SEGURA PARA STREAMLIT
# ============================================================

def analizar_pdf_streamlit(
    archivo_subido
) -> dict:
    """
    Permite utilizar st.file_uploader directamente.

    Guarda temporalmente el archivo, procesa el PDF y elimina
    el archivo temporal.
    """

    import os
    import tempfile

    if archivo_subido is None:

        raise ValueError(
            "No se recibió ningún archivo PDF."
        )

    if not archivo_subido.name.lower().endswith(
        ".pdf"
    ):

        raise PDFInvalidoError(
            "El archivo debe ser un PDF."
        )

    archivo_temporal = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temporal:

            temporal.write(
                archivo_subido.getbuffer()
            )

            archivo_temporal = temporal.name

        resultado = analizar_pdf(
            archivo_temporal
        )

        return resultado

    finally:

        if archivo_temporal and os.path.exists(
            archivo_temporal
        ):

            try:
                os.remove(
                    archivo_temporal
                )

            except OSError:
                pass
