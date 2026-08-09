```python
# ============================================================
# PENSION 40
# calculador.py
# ============================================================
#
# MOTOR MATEMÁTICO DEL SISTEMA
#
# Este módulo NO controla la interfaz.
#
# Recibe los datos obtenidos por extractor.py y calcula:
#
# - Grupo salarial
# - Cuantía básica
# - Incrementos anuales
# - Semanas adicionales
# - Porcentaje por edad
# - Factor 1.11
# - Asignaciones familiares
# - Pensión estimada
# - Salario para Modalidad 40
# - Costo mensual de Modalidad 40
# - Proyección 2026-2030
# - Inversión acumulada
# - ROI
#
# ============================================================

from math import floor
from typing import Optional


# ============================================================
# CONSTANTES GENERALES
# ============================================================

ANIO_ACTUAL = 2026

SEMANAS_MINIMAS = 500
SEMANAS_BASE = 500

DIAS_ANIO = 365
MESES_ANIO = 12

# Factor que utilizaremos para el incremento indicado
# en el modelo comercial de Pensión 40.
FACTOR_FOX = 1.11

# Tope de salario para Modalidad 40:
# 25 UMAs.
TOPE_UMA_M40 = 25


# ============================================================
# TASAS MODALIDAD 40
# ============================================================
#
# Tasas proporcionadas para el modelo 2026-2030.
#
# IMPORTANTE:
# Estas tasas quedan centralizadas para poder actualizarlas
# posteriormente sin modificar el resto del motor.
#
# ============================================================

TASAS_MODALIDAD_40 = {
    2026: 0.14438,
    2027: 0.15531,
    2028: 0.16624,
    2029: 0.17717,
    2030: 0.18810,
}


# ============================================================
# TABLA LEY 73
# ============================================================
#
# Artículo 167 de la Ley del Seguro Social de 1973:
#
# grupo salarial
# cuantía básica
# incremento anual
#
# El IMSS conserva esta tabla para el cálculo de las pensiones
# bajo Ley 73.
#
# ============================================================

TABLA_LEY_73 = [
    {
        "hasta": 1.00,
        "cuantia_basica": 0.8000,
        "incremento_anual": 0.00563,
    },
    {
        "hasta": 1.25,
        "cuantia_basica": 0.7711,
        "incremento_anual": 0.00814,
    },
    {
        "hasta": 1.50,
        "cuantia_basica": 0.5818,
        "incremento_anual": 0.01178,
    },
    {
        "hasta": 1.75,
        "cuantia_basica": 0.4923,
        "incremento_anual": 0.01430,
    },
    {
        "hasta": 2.00,
        "cuantia_basica": 0.4267,
        "incremento_anual": 0.01615,
    },
    {
        "hasta": 2.25,
        "cuantia_basica": 0.3765,
        "incremento_anual": 0.01756,
    },
    {
        "hasta": 2.50,
        "cuantia_basica": 0.3368,
        "incremento_anual": 0.01868,
    },
    {
        "hasta": 2.75,
        "cuantia_basica": 0.3048,
        "incremento_anual": 0.01958,
    },
    {
        "hasta": 3.00,
        "cuantia_basica": 0.2783,
        "incremento_anual": 0.02033,
    },
    {
        "hasta": 3.25,
        "cuantia_basica": 0.2560,
        "incremento_anual": 0.02096,
    },
    {
        "hasta": 3.50,
        "cuantia_basica": 0.2370,
        "incremento_anual": 0.02149,
    },
    {
        "hasta": 3.75,
        "cuantia_basica": 0.2207,
        "incremento_anual": 0.02195,
    },
    {
        "hasta": 4.00,
        "cuantia_basica": 0.2065,
        "incremento_anual": 0.02235,
    },
    {
        "hasta": 4.25,
        "cuantia_basica": 0.1939,
        "incremento_anual": 0.02271,
    },
    {
        "hasta": 4.50,
        "cuantia_basica": 0.1829,
        "incremento_anual": 0.02302,
    },
    {
        "hasta": 4.75,
        "cuantia_basica": 0.1730,
        "incremento_anual": 0.02330,
    },
    {
        "hasta": 5.00,
        "cuantia_basica": 0.1641,
        "incremento_anual": 0.02355,
    },
    {
        "hasta": 5.25,
        "cuantia_basica": 0.1561,
        "incremento_anual": 0.02377,
    },
    {
        "hasta": 5.50,
        "cuantia_basica": 0.1488,
        "incremento_anual": 0.02398,
    },
    {
        "hasta": 5.75,
        "cuantia_basica": 0.1422,
        "incremento_anual": 0.02416,
    },
    {
        "hasta": 6.00,
        "cuantia_basica": 0.1362,
        "incremento_anual": 0.02433,
    },
    {
        "hasta": float("inf"),
        "cuantia_basica": 0.1300,
        "incremento_anual": 0.02450,
    },
]


# ============================================================
# EDAD DE RETIRO
# ============================================================

PORCENTAJE_EDAD = {
    60: 0.75,
    61: 0.80,
    62: 0.85,
    63: 0.90,
    64: 0.95,
    65: 1.00,
}


# ============================================================
# EXCEPCIONES
# ============================================================

class CalculadorPensionError(Exception):
    """Error general del motor de cálculo."""
    pass


class EdadInvalidaError(CalculadorPensionError):
    """Edad fuera del rango permitido."""
    pass


class SBCInvalidoError(CalculadorPensionError):
    """SBC inválido."""
    pass


class SemanasInvalidasError(CalculadorPensionError):
    """Semanas insuficientes o inválidas."""
    pass


# ============================================================
# UTILIDADES
# ============================================================

def redondear(valor, decimales=2):
    """
    Redondeo centralizado del sistema.
    """
    return round(float(valor), decimales)


def validar_sbc(sbc_promedio: float):
    """
    Valida el SBC promedio.
    """

    try:
        sbc = float(sbc_promedio)
    except (TypeError, ValueError):

        raise SBCInvalidoError(
            "El SBC promedio no es numérico."
        )

    if sbc <= 0:

        raise SBCInvalidoError(
            "El SBC promedio debe ser mayor que cero."
        )

    return sbc


def validar_semanas(semanas: float):
    """
    Valida semanas cotizadas.
    """

    try:
        semanas = float(semanas)
    except (TypeError, ValueError):

        raise SemanasInvalidasError(
            "Las semanas cotizadas no son válidas."
        )

    if semanas < SEMANAS_MINIMAS:

        raise SemanasInvalidasError(
            f"El asegurado tiene {semanas:g} semanas. "
            f"Se requieren al menos {SEMANAS_MINIMAS}."
        )

    return semanas


def validar_edad(edad: int):
    """
    Valida edad de retiro.

    Para el cálculo principal de cesantía/vejez
    utilizamos 60 a 65 años.
    """

    try:
        edad = int(edad)
    except (TypeError, ValueError):

        raise EdadInvalidaError(
            "La edad no es válida."
        )

    if edad < 60 or edad > 65:

        raise EdadInvalidaError(
            "La edad para este escenario debe estar "
            "entre 60 y 65 años."
        )

    return edad


# ============================================================
# GRUPO SALARIAL
# ============================================================

def obtener_grupo_salarial(
    sbc_promedio: float,
    uma: float
) -> dict:
    """
    Determina el grupo salarial.

    Se compara el SBC diario contra la UMA configurada
    por el sistema.

    Retorna:

        multiplicador
        grupo
        cuantía básica
        incremento anual
    """

    sbc = validar_sbc(sbc_promedio)

    try:
        uma = float(uma)
    except (TypeError, ValueError):

        raise ValueError(
            "La UMA no es válida."
        )

    if uma <= 0:

        raise ValueError(
            "La UMA debe ser mayor que cero."
        )

    multiplicador = sbc / uma

    for fila in TABLA_LEY_73:

        if multiplicador <= fila["hasta"]:

            if fila["hasta"] == float("inf"):
                grupo = "6.01 o más"
            else:
                grupo = f"Hasta {fila['hasta']:.2f} UMA"

            return {
                "multiplicador_uma": redondear(
                    multiplicador,
                    4
                ),
                "grupo": grupo,
                "limite_grupo": fila["hasta"],
                "cuantia_basica": fila[
                    "cuantia_basica"
                ],
                "incremento_anual": fila[
                    "incremento_anual"
                ],
            }

    # Nunca debería llegar aquí.
    raise CalculadorPensionError(
        "No fue posible determinar el grupo salarial."
    )


# ============================================================
# SEMANAS ADICIONALES
# ============================================================

def calcular_semanas_adicionales(
    semanas: float
) -> dict:
    """
    Calcula las semanas posteriores a las primeras 500.

    La Ley 73 considera incrementos anuales por cada 52
    semanas adicionales después de las primeras 500.
    """

    semanas = validar_semanas(semanas)

    semanas_adicionales = max(
        0,
        semanas - SEMANAS_BASE
    )

    incrementos_anuales = floor(
        semanas_adicionales / 52
    )

    semanas_utilizadas = (
        SEMANAS_BASE +
        incrementos_anuales * 52
    )

    semanas_sobrantes = max(
        0,
        semanas - semanas_utilizadas
    )

    return {
        "semanas_totales": redondear(
            semanas,
            2
        ),
        "semanas_base": SEMANAS_BASE,
        "semanas_adicionales": redondear(
            semanas_adicionales,
            2
        ),
        "incrementos_anuales": incrementos_anuales,
        "semanas_sobrantes": redondear(
            semanas_sobrantes,
            2
        ),
    }


# ============================================================
# PORCENTAJE POR EDAD
# ============================================================

def porcentaje_por_edad(edad: int) -> float:
    """
    Obtiene el porcentaje correspondiente a la edad.

    60 = 75%
    61 = 80%
    62 = 85%
    63 = 90%
    64 = 95%
    65 = 100%
    """

    edad = validar_edad(edad)

    return PORCENTAJE_EDAD[edad]


# ============================================================
# ASIGNACIONES FAMILIARES
# ============================================================

def calcular_asignacion_familiar(
    pension_base: float,
    tipo_asignacion: str = "ninguna"
) -> dict:
    """
    Calcula la asignación familiar.

    Opciones:

    ninguna
    esposa
    esposo
    conyuge
    hijo
    hijos
    padre
    madre
    padres
    asistencia

    Valores configurados:

    Cónyuge = 15%
    Hijos = 10%
    Padres = 10%
    Ayuda asistencial = 10%

    El porcentaje puede modificarse posteriormente
    desde el motor si la interpretación jurídica del
    escenario específico requiere otro tratamiento.
    """

    pension_base = float(pension_base)

    tipo = (
        str(tipo_asignacion or "ninguna")
        .strip()
        .lower()
    )

    porcentajes = {
        "ninguna": 0.00,
        "esposa": 0.15,
        "esposo": 0.15,
        "conyuge": 0.15,
        "hijo": 0.10,
        "hijos": 0.10,
        "padre": 0.10,
        "madre": 0.10,
        "padres": 0.10,
        "asistencia": 0.10,
    }

    porcentaje = porcentajes.get(
        tipo,
        0.00
    )

    monto = (
        pension_base *
        porcentaje
    )

    return {
        "tipo": tipo,
        "porcentaje": porcentaje,
        "monto": redondear(monto),
    }


# ============================================================
# PENSIÓN BASE LEY 73
# ============================================================

def calcular_pension_base(
    sbc_promedio: float,
    semanas: float,
    edad: int,
    uma: float
) -> dict:
    """
    Calcula la pensión base bajo el esquema Ley 73.

    Fórmula simplificada del motor:

        SBC promedio
        x cuantía básica
        +
        SBC promedio
        x incremento anual
        x número de incrementos

    El resultado diario se convierte a mensual usando:

        365 / 12
    """

    sbc = validar_sbc(
        sbc_promedio
    )

    semanas = validar_semanas(
        semanas
    )

    edad = validar_edad(
        edad
    )

    grupo = obtener_grupo_salarial(
        sbc,
        uma
    )

    incrementos = calcular_semanas_adicionales(
        semanas
    )

    porcentaje_edad = porcentaje_por_edad(
        edad
    )

    cuantia_basica = grupo[
        "cuantia_basica"
    ]

    incremento_anual = grupo[
        "incremento_anual"
    ]

    numero_incrementos = incrementos[
        "incrementos_anuales"
    ]

    porcentaje_total = (
        cuantia_basica
        +
        (
            incremento_anual *
            numero_incrementos
        )
    )

    pension_diaria_65 = (
        sbc *
        porcentaje_total
    )

    pension_mensual_65 = (
        pension_diaria_65 *
        DIAS_ANIO /
        MESES_ANIO
    )

    pension_diaria_edad = (
        pension_diaria_65 *
        porcentaje_edad
    )

    pension_mensual_edad = (
        pension_mensual_65 *
        porcentaje_edad
    )

    return {
        "sbc_promedio": redondear(sbc),
        "uma": redondear(uma),
        "grupo_salarial": grupo[
            "grupo"
        ],
        "multiplicador_uma": grupo[
            "multiplicador_uma"
        ],
        "cuantia_basica": cuantia_basica,
        "incremento_anual": incremento_anual,
        "incrementos_anuales": numero_incrementos,
        "porcentaje_total": redondear(
            porcentaje_total * 100,
            4
        ),
        "pension_diaria_65": redondear(
            pension_diaria_65
        ),
        "pension_mensual_65": redondear(
            pension_mensual_65
        ),
        "edad": edad,
        "porcentaje_edad": redondear(
            porcentaje_edad * 100,
            2
        ),
        "pension_diaria_edad": redondear(
            pension_diaria_edad
        ),
        "pension_mensual_edad": redondear(
            pension_mensual_edad
        ),
    }


# ============================================================
# FACTOR FOX
# ============================================================

def aplicar_factor_fox(
    pension_mensual: float,
    factor: float = FACTOR_FOX
) -> dict:
    """
    Aplica el factor 1.11 utilizado por el modelo Pensión 40.
    """

    pension_mensual = float(
        pension_mensual
    )

    resultado = (
        pension_mensual *
        factor
    )

    incremento = (
        resultado -
        pension_mensual
    )

    return {
        "factor": factor,
        "pension_anterior": redondear(
            pension_mensual
        ),
        "incremento": redondear(
            incremento
        ),
        "pension_con_factor": redondear(
            resultado
        ),
    }


# ============================================================
# PENSIÓN FINAL
# ============================================================

def calcular_pension_final(
    sbc_promedio: float,
    semanas: float,
    edad: int,
    uma: float,
    tipo_asignacion: str = "ninguna",
    aplicar_fox: bool = True
) -> dict:
    """
    Ejecuta todo el cálculo de pensión.

    Orden:

    1. Ley 73
    2. Edad
    3. Factor Fox
    4. Asignación familiar
    """

    base = calcular_pension_base(
        sbc_promedio=sbc_promedio,
        semanas=semanas,
        edad=edad,
        uma=uma
    )

    pension = base[
        "pension_mensual_edad"
    ]

    if aplicar_fox:

        fox = aplicar_factor_fox(
            pension
        )

        pension_con_fox = fox[
            "pension_con_factor"
        ]

    else:

        fox = {
            "factor": 1.0,
            "pension_anterior":
                pension,
            "incremento": 0,
            "pension_con_factor":
                pension
        }

        pension_con_fox = pension

    asignacion = calcular_asignacion_familiar(
        pension_con_fox,
        tipo_asignacion
    )

    pension_final = (
        pension_con_fox +
        asignacion["monto"]
    )

    return {
        **base,
        "factor_fox": fox,
        "asignacion_familiar":
            asignacion,
        "pension_final_mensual":
            redondear(pension_final),
        "pension_final_anual":
            redondear(
                pension_final * 12
            ),
    }


# ============================================================
# MODALIDAD 40 - SALARIO A COTIZAR
# ============================================================

def calcular_salario_m40(
    sbc_m40: float,
    uma: float
) -> dict:
    """
    Determina el salario diario que se utilizará para
    Modalidad 40.

    El sistema limita el salario a 25 UMAs.
    """

    try:
        sbc_m40 = float(
            sbc_m40
        )
        uma = float(
            uma
        )
    except (TypeError, ValueError):

        raise ValueError(
            "SBC o UMA inválidos."
        )

    if sbc_m40 <= 0:
        raise ValueError(
            "El salario de Modalidad 40 debe ser mayor que cero."
        )

    if uma <= 0:
        raise ValueError(
            "La UMA debe ser mayor que cero."
        )

    tope_diario = (
        uma *
        TOPE_UMA_M40
    )

    salario_aplicado = min(
        sbc_m40,
        tope_diario
    )

    return {
        "sbc_solicitado": redondear(
            sbc_m40
        ),
        "tope_25_uma": redondear(
            tope_diario
        ),
        "sbc_aplicado": redondear(
            salario_aplicado
        ),
        "topado": sbc_m40 > tope_diario,
    }


# ============================================================
# COSTO MENSUAL MODALIDAD 40
# ============================================================

def calcular_costo_m40_mensual(
    salario_diario: float,
    tasa: float
) -> float:
    """
    Calcula el costo mensual aproximado.

    Base:

        salario diario
        x 30.4 días
        x tasa
    """

    salario_diario = float(
        salario_diario
    )

    tasa = float(
        tasa
    )

    costo = (
        salario_diario *
        30.4 *
        tasa
    )

    return redondear(
        costo
    )


# ============================================================
# PROYECCIÓN MODALIDAD 40
# ============================================================

def proyectar_modalidad_40(
    salario_diario: float,
    uma: float,
    anio_inicio: int = 2026,
    anio_fin: int = 2030
) -> list:
    """
    Genera la proyección anual de costos de Modalidad 40.

    Para cada año calcula:

    - tasa
    - salario diario aplicado
    - costo mensual
    - costo anual
    """

    salario = calcular_salario_m40(
        salario_diario,
        uma
    )

    salario_aplicado = salario[
        "sbc_aplicado"
    ]

    proyeccion = []

    for anio in range(
        anio_inicio,
        anio_fin + 1
    ):

        tasa = TASAS_MODALIDAD_40.get(
            anio,
            TASAS_MODALIDAD_40[2030]
        )

        costo_mensual = (
            calcular_costo_m40_mensual(
                salario_aplicado,
                tasa
            )
        )

        costo_anual = (
            costo_mensual *
            12
        )

        proyeccion.append(
            {
                "anio": anio,
                "tasa": redondear(
                    tasa * 100,
                    3
                ),
                "salario_diario":
                    redondear(
                        salario_aplicado
                    ),
                "costo_mensual":
                    redondear(
                        costo_mensual
                    ),
                "costo_anual":
                    redondear(
                        costo_anual
                    ),
            }
        )

    return proyeccion


# ============================================================
# INVERSIÓN DE MODALIDAD 40
# ============================================================

def calcular_inversion_m40(
    salario_diario: float,
    uma: float,
    meses: int,
    anio_inicio: int = 2026
) -> dict:
    """
    Calcula la inversión de Modalidad 40 durante determinado
    número de meses.

    Los meses se distribuyen entre años para aplicar las
    diferentes tasas.
    """

    if meses <= 0:

        raise ValueError(
            "Los meses deben ser mayores que cero."
        )

    salario = calcular_salario_m40(
        salario_diario,
        uma
    )

    salario_aplicado = salario[
        "sbc_aplicado"
    ]

    filas = []

    acumulado = 0.0

    for numero_mes in range(
        1,
        meses + 1
    ):

        anio = (
            anio_inicio +
            ((numero_mes - 1) // 12)
        )

        tasa = TASAS_MODALIDAD_40.get(
            anio,
            TASAS_MODALIDAD_40[2030]
        )

        costo = calcular_costo_m40_mensual(
            salario_aplicado,
            tasa
        )

        acumulado += costo

        filas.append(
            {
                "mes": numero_mes,
                "anio": anio,
                "tasa": redondear(
                    tasa * 100,
                    3
                ),
                "costo_mensual":
                    redondear(costo),
                "inversion_acumulada":
                    redondear(acumulado),
            }
        )

    return {
        "salario_diario":
            redondear(
                salario_aplicado
            ),
        "meses": meses,
        "inversion_total":
            redondear(acumulado),
        "tabla_mensual": filas,
    }


# ============================================================
# ROI
# ============================================================

def calcular_roi(
    inversion_total: float,
    pension_mensual: float
) -> dict:
    """
    Calcula el tiempo estimado de recuperación de la inversión.

    ROI simple:

        inversión / incremento mensual

    En esta primera versión consideramos la pensión final
    como flujo mensual de referencia.

    Posteriormente podremos agregar:

    - pensión sin Modalidad 40
    - pensión con Modalidad 40
    - incremento mensual real
    - inflación
    - valor presente
    """

    inversion_total = float(
        inversion_total
    )

    pension_mensual = float(
        pension_mensual
    )

    if pension_mensual <= 0:

        return {
            "meses": None,
            "anios": None,
            "mensaje":
                "No fue posible calcular el ROI."
        }

    meses = (
        inversion_total /
        pension_mensual
    )

    return {
        "meses": redondear(
            meses,
            1
        ),
        "anios": redondear(
            meses / 12,
            2
        ),
        "mensaje":
            "Tiempo estimado de recuperación "
            "de la inversión."
    }


# ============================================================
# ESCENARIO COMPLETO
# ============================================================

def calcular_escenario(
    sbc_promedio: float,
    semanas: float,
    edad: int,
    uma: float,
    tipo_asignacion: str = "ninguna",
    salario_modalidad_40: Optional[float] = None,
    meses_modalidad_40: int = 60,
    aplicar_fox: bool = True
) -> dict:
    """
    Función PRINCIPAL que utilizará app.py.

    Parámetros:

        sbc_promedio
            Promedio de las últimas 250 semanas.

        semanas
            Semanas totales.

        edad
            Edad de retiro.

        uma
            UMA configurada.

        tipo_asignacion
            esposa / esposo / hijos / etc.

        salario_modalidad_40
            Salario diario que desea utilizar en M40.

        meses_modalidad_40
            Duración de la estrategia.

    Retorna todo el escenario financiero.
    """

    sbc = validar_sbc(
        sbc_promedio
    )

    semanas = validar_semanas(
        semanas
    )

    edad = validar_edad(
        edad
    )

    # --------------------------------------------------------
    # Si no se especifica salario M40,
    # utilizamos como referencia el SBC promedio.
    # --------------------------------------------------------

    if salario_modalidad_40 is None:

        salario_modalidad_40 = sbc

    # --------------------------------------------------------
    # PENSIÓN
    # --------------------------------------------------------

    pension = calcular_pension_final(
        sbc_promedio=sbc,
        semanas=semanas,
        edad=edad,
        uma=uma,
        tipo_asignacion=tipo_asignacion,
        aplicar_fox=aplicar_fox
    )

    # --------------------------------------------------------
    # SALARIO M40
    # --------------------------------------------------------

    salario_m40 = calcular_salario_m40(
        salario_modalidad_40,
        uma
    )

    # --------------------------------------------------------
    # PROYECCIÓN ANUAL
    # --------------------------------------------------------

    proyeccion_anual = proyectar_modalidad_40(
        salario_diario=salario_m40[
            "sbc_aplicado"
        ],
        uma=uma,
        anio_inicio=ANIO_ACTUAL,
        anio_fin=2030
    )

    # --------------------------------------------------------
    # INVERSIÓN MENSUAL
    # --------------------------------------------------------

    inversion = calcular_inversion_m40(
        salario_diario=salario_m40[
            "sbc_aplicado"
        ],
        uma=uma,
        meses=meses_modalidad_40,
        anio_inicio=ANIO_ACTUAL
    )

    # --------------------------------------------------------
    # ROI
    # --------------------------------------------------------

    roi = calcular_roi(
        inversion_total=inversion[
            "inversion_total"
        ],
        pension_mensual=pension[
            "pension_final_mensual"
        ]
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {
        "version_motor":
            "Pension40-2026-1.0",

        "parametros": {
            "sbc_promedio":
                redondear(sbc),
            "semanas":
                redondear(semanas),
            "edad":
                edad,
            "uma":
                redondear(uma),
            "tipo_asignacion":
                tipo_asignacion,
            "salario_modalidad_40":
                salario_m40[
                    "sbc_aplicado"
                ],
            "meses_modalidad_40":
                meses_modalidad_40,
        },

        "pension": pension,

        "modalidad_40": {
            "salario":
                salario_m40,
            "proyeccion_anual":
                proyeccion_anual,
            "inversion":
                inversion,
        },

        "roi": roi,
    }


# ============================================================
# FUNCIÓN PARA MOSTRAR RESUMEN
# ============================================================

def resumen_escenario(
    resultado: dict
) -> dict:
    """
    Devuelve únicamente los datos principales para que
    app.py pueda mostrarlos en pantalla.
    """

    pension = resultado[
        "pension"
    ]

    m40 = resultado[
        "modalidad_40"
    ]

    roi = resultado[
        "roi"
    ]

    return {
        "SBC promedio":
            pension[
                "sbc_promedio"
            ],

        "Semanas cotizadas":
            resultado[
                "parametros"
            ][
                "semanas"
            ],

        "Edad":
            pension[
                "edad"
            ],

        "Grupo salarial":
            pension[
                "grupo_salarial"
            ],

        "Cuantía básica":
            f"{pension['cuantia_basica'] * 100:.2f}%",

        "Incrementos anuales":
            pension[
                "incrementos_anuales"
            ],

        "Porcentaje por edad":
            f"{pension['porcentaje_edad']:.0f}%",

        "Factor Fox":
            f"{pension['factor_fox']['factor']:.2f}",

        "Asignación familiar":
            f"{pension['asignacion_familiar']['porcentaje'] * 100:.0f}%",

        "Pensión estimada mensual":
            pension[
                "pension_final_mensual"
            ],

        "Salario Modalidad 40":
            m40[
                "salario"
            ][
                "sbc_aplicado"
            ],

        "Inversión Modalidad 40":
            m40[
                "inversion"
            ][
                "inversion_total"
            ],

        "ROI estimado meses":
            roi[
                "meses"
            ],
    }


# ============================================================
# PRUEBA RÁPIDA DEL MOTOR
# ============================================================
#
# Este bloque NO se ejecuta cuando se importa desde app.py.
#
# Puede ejecutarse directamente para comprobar que el archivo
# funciona.
#
# ============================================================

if __name__ == "__main__":

    print(
        "======================================"
    )

    print(
        "PENSION 40 - PRUEBA DEL CALCULADOR"
    )

    print(
        "======================================"
    )

    # Ejemplo de prueba.
    #
    # Estos valores son solamente para comprobar
    # que el motor funciona.

    try:

        resultado = calcular_escenario(
            sbc_promedio=629.59,
            semanas=1681,
            edad=65,
            uma=117.31,
            tipo_asignacion="conyuge",
            salario_modalidad_40=2932.75,
            meses_modalidad_40=60,
            aplicar_fox=True
        )

        resumen = resumen_escenario(
            resultado
        )

        for clave, valor in resumen.items():

            print(
                f"{clave}: {valor}"
            )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )
```
