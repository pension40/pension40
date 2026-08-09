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
    Busca el nombre del asegurado (titular de la Constancia).

    IMPORTANTE:
    La Constancia de Semanas Cotizadas del IMSS NO utiliza una
    etiqueta "NOMBRE:" o "ASEGURADO:" para el titular; el nombre
    aparece suelto en el bloque que sigue a "Estimado(a),"
    hasta llegar a la etiqueta "NSS". Ese bloque también
    contiene texto de la tabla vecina (fecha de emisión,
    encabezados "DD MM YYYY", etc.), intercalado por el layout
    de dos columnas del PDF, así que no se puede anclar de
    forma rígida entre ambas etiquetas.

    Cada registro del historial laboral además contiene la
    etiqueta "Nombre del patrón", que un regex genérico de
    "NOMBRE" capturaría por error (coincide primero en el
    texto y no es el nombre del asegurado, sino el de un
    empleador cualquiera).

    Estrategia:
    1. Aislar el bloque de texto entre "Estimado(a)," y "NSS".
    2. Dentro de ese bloque, evaluar cada línea y descartar las
       que son ruido conocido (fechas, encabezados DD/MM/YYYY,
       o líneas con dígitos).
    3. Quedarse con la línea restante que más parece un nombre
       de persona (2 o más palabras, solo letras y espacios).
    """

    idx_estimado = re.search(
        r"Estimado\(a\)",
        texto,
        re.IGNORECASE
    )

    idx_nss = re.search(
        r"\bNSS\b",
        texto,
        re.IGNORECASE
    )

    if idx_estimado and idx_nss and idx_nss.start() > idx_estimado.end():

        bloque = texto[idx_estimado.end():idx_nss.start()]

        ruido_conocido = {
            "DD MM YYYY",
            "DD/MM/YYYY",
        }

        candidatos = []

        for linea in bloque.split("\n"):

            linea_limpia = linea.strip(" ,:\t")

            if not linea_limpia:
                continue

            if linea_limpia.upper() in ruido_conocido:
                continue

            # Descartar líneas con dígitos (fechas, folios, etc.)
            if re.search(r"\d", linea_limpia):
                continue

            # Descartar líneas que contienen palabras de ruido
            # típicas de encabezados de tabla vecinos.
            if re.search(
                r"FECHA|EMISI[ÓO]N|REPORTE",
                linea_limpia,
                re.IGNORECASE
            ):
                continue

            # El nombre real es solo letras/acentos y espacios,
            # con al menos dos palabras.
            if re.fullmatch(
                r"[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,}",
                linea_limpia
            ) and len(linea_limpia.split()) >= 2:

                candidatos.append(linea_limpia)

        if candidatos:

            # Se toma el candidato más largo: es la heurística
            # más simple para preferir un nombre completo sobre
            # fragmentos de ruido residual.
            mejor_candidato = max(
                candidatos,
                key=len
            )

            nombre = limpiar_texto(
                mejor_candidato
            )

            if nombre:
                return nombre.strip()

    # --------------------------------------------------------
    # RESPALDO: otras etiquetas explícitas de nombre
    #
    # Se excluye "del patrón" para no capturar por error el
    # nombre de un empleador del historial laboral.
    # --------------------------------------------------------

    patrones = [
        r"NOMBRE\s*[:\-]?\s*(?!DEL\s+PATR)([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s]{5,})",
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
# CURP Y FECHA DE NACIMIENTO DERIVADA
# ============================================================

def extraer_curp(texto: str) -> Optional[str]:
    """
    Busca el CURP (18 caracteres alfanuméricos) del asegurado.
    """

    coincidencia = re.search(
        r"CURP\s*[:\-]?\s*([A-Z]{4}\d{6}[A-Z]{6}[A-Z0-9]\d)",
        texto,
        re.IGNORECASE
    )

    if coincidencia:
        return coincidencia.group(1).upper()

    return None


def calcular_fecha_nacimiento_desde_curp(
    curp: str
) -> Optional[datetime]:
    """
    Deriva la fecha de nacimiento a partir del CURP.

    La Constancia de Semanas Cotizadas del IMSS no incluye una
    etiqueta explícita de "fecha de nacimiento", pero el CURP
    siempre está presente y la codifica en sus posiciones 5-10
    (AAMMDD), por lo que es la fuente más confiable disponible
    en este documento.

    Regla oficial de RENAPO para el siglo (posición 17, índice
    16 en base 0):
        - Dígito (0-9): nació antes del año 2000 (siglo XX).
        - Letra (A-Z): nació en el año 2000 o después (XXI).
    """

    if not curp or len(curp) < 17:
        return None

    try:

        aa = int(curp[4:6])
        mm = int(curp[6:8])
        dd = int(curp[8:10])

    except ValueError:

        return None

    caracter_siglo = curp[16]

    if caracter_siglo.isdigit():
        anio = 1900 + aa
    else:
        anio = 2000 + aa

    try:

        return datetime(anio, mm, dd)

    except ValueError:

        return None


# ============================================================
# FECHA DE NACIMIENTO
# ============================================================

# ============================================================
# FECHA DE EMISIÓN DEL REPORTE
# ============================================================

def extraer_fecha_emision(
    texto: str
) -> Optional[datetime]:
    """
    Busca la fecha de emisión del reporte.

    Se usa como fecha de referencia para calcular la duración
    de empleos que siguen "Vigente" (sin fecha de baja), y así
    no subestimar su peso en el cálculo del SBC promedio.

    Formato en el documento: "DD / MM / YYYY" con la etiqueta
    "DD MM YYYY" justo debajo.
    """

    patron = (
        r"Fecha\s+de\s+emisi[óo]n\s+del\s+reporte"
        r"\s*\n?\s*"
        r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})"
    )

    coincidencia = re.search(
        patron,
        texto,
        re.IGNORECASE
    )

    if coincidencia:

        dia, mes, anio = coincidencia.groups()

        fecha = convertir_fecha(
            f"{dia}/{mes}/{anio}"
        )

        if fecha:
            return fecha

    return None


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
    texto: str,
    historial_laboral: Optional[list] = None
) -> Optional[datetime]:
    """
    Determina la primera fecha de cotización del asegurado.

    FUENTE PRIMARIA (confiable):
        El historial laboral estructurado (extraído de las
        tablas del PDF) contiene un registro por cada periodo
        laboral, con su "fecha_inicio" ya calculada. La primera
        cotización real es la fecha de inicio MÍNIMA de todos
        los registros, sin importar el orden en que aparezcan
        en el documento.

        La Constancia de Semanas Cotizadas del IMSS lista los
        empleos del más reciente al más antiguo, por lo que
        buscar la fecha con un regex de texto libre (ver más
        abajo) captura por error la fecha de alta del empleo
        MÁS RECIENTE, no la primera cotización real.

    RESPALDO (menos confiable):
        Si no se dispone del historial laboral (por ejemplo,
        el PDF no tiene tablas reconocibles), se intenta un
        regex de texto sobre frases explícitas. Este método
        puede fallar si el documento no contiene literalmente
        esas frases o si repite la etiqueta varias veces.
    """

    # --------------------------------------------------------
    # FUENTE PRIMARIA: historial laboral estructurado
    # --------------------------------------------------------

    if historial_laboral:

        fechas_inicio = [
            registro["fecha_inicio"]
            for registro in historial_laboral
            if registro.get("fecha_inicio") is not None
        ]

        if fechas_inicio:
            return min(fechas_inicio)

    # --------------------------------------------------------
    # RESPALDO: regex de texto libre
    # --------------------------------------------------------

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

    FUENTE PRIMARIA (confiable):
        La "Cadena original" que el IMSS incluye al final del
        documento (usada para el sello digital) contiene el
        texto literal "Número total de semanas cotizadas:N".
        Al formar parte de los datos firmados digitalmente,
        es la fuente más confiable del documento.

    RESPALDO (menos confiable):
        La tabla superior del documento también muestra
        "Total de semanas cotizadas" seguido del valor, pero
        en el texto plano extraído por pdfplumber el número
        puede terminar en una línea distinta a la etiqueta
        (por el layout de dos columnas), con otro texto del
        documento (como el CURP) intercalado. Por eso se exige
        que el número aparezca solo en su propia línea.
    """

    # --------------------------------------------------------
    # FUENTE PRIMARIA: cadena original firmada digitalmente
    # --------------------------------------------------------

    patron_cadena_original = (
        r"[Nn][uú]mero\s+total\s+de\s+semanas\s+cotizadas"
        r"\s*:\s*(\d+)"
    )

    coincidencia = re.search(
        patron_cadena_original,
        texto
    )

    if coincidencia:

        valor = convertir_numero(
            coincidencia.group(1)
        )

        if valor is not None:
            return valor

    # --------------------------------------------------------
    # RESPALDO: "Total de semanas cotizadas" + número en
    # su propia línea (tolera texto intermedio como el CURP)
    # --------------------------------------------------------

    patron_total_multilinea = (
        r"Total\s+de\s+semanas\s+cotizadas"
        r"[^\n]*\n"
        r"[^\n]*?(?:^|\s)(\d{1,5})\s*(?:\n|$)"
    )

    coincidencia = re.search(
        patron_total_multilinea,
        texto,
        re.IGNORECASE | re.MULTILINE
    )

    if coincidencia:

        valor = convertir_numero(
            coincidencia.group(1)
        )

        if valor is not None:
            return valor

    # --------------------------------------------------------
    # RESPALDO FINAL: patrones simples (mismo renglón)
    # --------------------------------------------------------

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
    Determina si una fila corresponde al ENCABEZADO de un
    periodo laboral (no a un movimiento dentro de ese periodo).

    IMPORTANTE:
    La Constancia de Semanas Cotizadas del IMSS presenta, por
    cada empleo, dos tablas distintas:

        1. Encabezado del empleo: Nombre del patrón, Registro
           Patronal, Entidad federativa, "Fecha de alta" /
           "Fecha de baja" y el SBC. Esta fila define el
           periodo laboral real.

        2. Movimientos del empleo: "Tipo de movimiento"
           (ALTA, BAJA, REINGRESO, MODIFICACION DE SALARIO),
           con su propia fecha. Estas filas son sub-eventos
           DENTRO del mismo periodo, no periodos nuevos.

    Un filtro que solo exige "contiene una fecha" deja pasar
    ambos tipos de fila. Esto genera registros fantasma de
    1 día (la fecha de un movimiento tratada como un periodo
    laboral completo), que contaminan el cálculo del SBC
    promedio ponderado por días.

    Por eso se exige la presencia explícita de la etiqueta
    "Fecha de alta", que solo aparece en el encabezado real
    del empleo.
    """

    if not fila:
        return False

    texto = " ".join(
        limpiar_texto(celda)
        for celda in fila
        if celda is not None
    )

    contiene_fecha_alta = bool(
        re.search(
            r"FECHA\s+DE\s+ALTA",
            texto,
            re.IGNORECASE
        )
    )

    if not contiene_fecha_alta:
        return False

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
    pagina: int,
    fecha_referencia: Optional[datetime] = None
) -> Optional[dict]:
    """
    Convierte una fila de encabezado de empleo en un registro
    laboral (fecha_inicio, fecha_fin, días, SBC).

    EMPLEO VIGENTE:
    Cuando el empleo sigue activo, la celda de "Fecha de baja"
    dice literalmente "Vigente" (sin fecha). En ese caso solo
    se encuentra la fecha de alta, y el periodo se calcularía
    erróneamente como de 1 solo día si no se usa una fecha de
    referencia como fin del periodo.

    Se usa "fecha_referencia" (la fecha de emisión del reporte,
    o la fecha actual si no se conoce) como fecha de baja
    implícita, para no subestimar el peso de un empleo vigente
    en el cálculo del SBC promedio ponderado por días.
    """

    if not fila:
        return None

    if not _fila_contiene_fecha(fila):
        return None

    fechas = _extraer_fechas_de_fila(fila)

    if not fechas:
        return None

    texto_fila = " ".join(
        limpiar_texto(celda)
        for celda in fila
        if celda is not None
    )

    es_vigente = bool(
        re.search(
            r"VIGENTE",
            texto_fila,
            re.IGNORECASE
        )
    )

    fecha_inicio = min(fechas)

    if es_vigente and len(fechas) == 1:

        fecha_fin = fecha_referencia or datetime.now()

    else:

        fecha_fin = max(fechas)

    sbc = _buscar_sbc(fila)

    dias = _buscar_numero_dias(fila)

    if dias is None:

        # Si existen dos fechas (o el empleo es vigente y se
        # usó la fecha de referencia), calculamos días
        # aproximados como respaldo.
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
    ruta_pdf: str,
    fecha_referencia: Optional[datetime] = None
) -> list:
    """
    Extrae registros laborales de todas las tablas.

    El resultado se ordena de lo más reciente a lo más antiguo.

    "fecha_referencia" se usa como fecha de baja implícita
    para empleos que siguen "Vigente" (ver
    normalizar_registro_laboral). Si no se proporciona, cada
    registro vigente usará la fecha actual del sistema.
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
                pagina,
                fecha_referencia=fecha_referencia
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

    curp = extraer_curp(
        texto
    )

    # --------------------------------------------------------
    # Fecha de nacimiento
    #
    # FUENTE PRIMARIA: derivada del CURP (siempre presente en
    # la Constancia). FUENTE RESPALDO: regex de texto libre,
    # para documentos que sí incluyan una etiqueta explícita
    # de "fecha de nacimiento".
    # --------------------------------------------------------

    fecha_nacimiento = None

    if curp:

        fecha_nacimiento = calcular_fecha_nacimiento_desde_curp(
            curp
        )

    if fecha_nacimiento is None:

        fecha_nacimiento = extraer_fecha_nacimiento(
            texto
        )

    fecha_emision = extraer_fecha_emision(
        texto
    )

    # --------------------------------------------------------
    # Historial laboral
    #
    # IMPORTANTE: se extrae ANTES de determinar la primera
    # fecha de cotización, porque es la fuente confiable para
    # ese dato (ver extraer_primera_fecha_cotizacion).
    #
    # Se pasa "fecha_emision" como referencia para calcular
    # correctamente la duración de empleos "Vigente".
    # --------------------------------------------------------

    historial = extraer_historial_laboral(
        ruta_pdf,
        fecha_referencia=fecha_emision
    )

    ultimas_250 = calcular_ultimas_250_semanas(
        historial
    )

    primera_fecha = (
        extraer_primera_fecha_cotizacion(
            texto,
            historial_laboral=historial
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

    edad_actual = None

    if fecha_nacimiento:

        hoy = datetime.now()

        edad_actual = (
            hoy.year - fecha_nacimiento.year
            - (
                (hoy.month, hoy.day)
                < (fecha_nacimiento.month, fecha_nacimiento.day)
            )
        )

    return {
        "nombre": nombre,
        "nss": nss,
        "curp": curp,
        "fecha_nacimiento":
            fecha_nacimiento,
        "edad_actual": edad_actual,
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
