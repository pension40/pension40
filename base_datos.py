# ============================================================
# PENSION 40
# base_datos.py
# ============================================================
#
# Módulo encargado de:
#
# - Conexión segura con Supabase
# - Registro de prospectos
# - Validación de códigos promocionales
# - Registro de uso de promociones
# - Lectura de configuraciones
# - Actualización de configuraciones
# - Administración de promociones
# - Verificación de contraseña administrativa
#
# IMPORTANTE:
# Las credenciales NUNCA deben escribirse aquí.
# Se obtienen desde Streamlit Secrets o variables de entorno.
# ============================================================

from datetime import datetime, timezone
import hashlib
import hmac
import os

import streamlit as st
from supabase import create_client, Client


# ============================================================
# CONFIGURACIÓN
# ============================================================

def _obtener_secreto(nombre: str, default=None):
    """
    Obtiene un secreto desde Streamlit Secrets.

    Para desarrollo local también intenta obtenerlo
    desde variables de entorno.
    """

    try:
        valor = st.secrets.get(nombre)

        if valor:
            return valor

    except Exception:
        pass

    return os.getenv(nombre, default)


# ============================================================
# CONEXIÓN SUPABASE
# ============================================================

@st.cache_resource
def obtener_cliente_supabase() -> Client:
    """
    Crea y conserva una conexión con Supabase.

    IMPORTANTE:
    Esta aplicación utiliza la SERVICE ROLE KEY porque
    el backend necesita realizar operaciones administrativas.

    La clave jamás debe publicarse en GitHub.
    """

    url = _obtener_secreto("SUPABASE_URL")
    key = _obtener_secreto("SUPABASE_SERVICE_ROLE_KEY")

    if not url:
        raise RuntimeError(
            "No se encontró SUPABASE_URL en los Secrets."
        )

    if not key:
        raise RuntimeError(
            "No se encontró SUPABASE_SERVICE_ROLE_KEY "
            "en los Secrets."
        )

    return create_client(url, key)


# ============================================================
# FUNCIÓN AUXILIAR
# ============================================================

def _cliente() -> Client:
    """
    Devuelve el cliente Supabase.
    """
    return obtener_cliente_supabase()


# ============================================================
# PROSPECTOS
# ============================================================

def guardar_prospecto(
    nombre: str,
    correo: str,
    telefono: str,
    nss: str = None,
    semanas_cotizadas: int = None,
    sbc_promedio: float = None,
    fecha_nacimiento=None,
    estatus_pago: bool = False,
    codigo_promocional: str = None
):
    """
    Inserta un nuevo prospecto en prospectos_pension.

    Retorna:
        dict con el registro creado.
    """

    if not nombre or not nombre.strip():
        raise ValueError("El nombre es obligatorio.")

    if not correo or not correo.strip():
        raise ValueError("El correo es obligatorio.")

    datos = {
        "nombre": nombre.strip(),
        "correo": correo.strip().lower(),
        "telefono": telefono.strip() if telefono else None,
        "nss": nss.strip() if nss else None,
        "semanas_cotizadas": semanas_cotizadas,
        "sbc_promedio": sbc_promedio,
        "fecha_nacimiento": fecha_nacimiento,
        "estatus_pago": bool(estatus_pago),
        "codigo_promocional": (
            codigo_promocional.strip().upper()
            if codigo_promocional
            else None
        ),
        "fecha_actualizacion": datetime.now(timezone.utc).isoformat()
    }

    respuesta = (
        _cliente()
        .table("prospectos_pension")
        .insert(datos)
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError(
            "Supabase no devolvió el prospecto creado."
        )

    return respuesta.data[0]


# ============================================================
# ACTUALIZAR PROSPECTO
# ============================================================

def actualizar_prospecto(
    prospecto_id: str,
    datos: dict
):
    """
    Actualiza información de un prospecto.
    """

    datos = dict(datos)

    datos["fecha_actualizacion"] = (
        datetime.now(timezone.utc).isoformat()
    )

    respuesta = (
        _cliente()
        .table("prospectos_pension")
        .update(datos)
        .eq("id", prospecto_id)
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError(
            "No se encontró el prospecto para actualizar."
        )

    return respuesta.data[0]


# ============================================================
# MARCAR PAGO
# ============================================================

def marcar_pago_confirmado(prospecto_id: str):
    """
    Marca el reporte del prospecto como pagado.
    """

    return actualizar_prospecto(
        prospecto_id,
        {
            "estatus_pago": True
        }
    )


# ============================================================
# BUSCAR PROSPECTO
# ============================================================

def obtener_prospecto(prospecto_id: str):
    """
    Obtiene un prospecto por UUID.
    """

    respuesta = (
        _cliente()
        .table("prospectos_pension")
        .select("*")
        .eq("id", prospecto_id)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        return None

    return respuesta.data[0]


# ============================================================
# CÓDIGOS PROMOCIONALES
# ============================================================

def validar_codigo_promocional(codigo: str):
    """
    Valida un código promocional.

    Comprueba:

    1. Que exista.
    2. Que esté ACTIVO.
    3. Que la fecha de inicio sea válida.
    4. Que no haya expirado.
    5. Que no haya superado su límite de usos.

    Retorna:

        {
            "valido": True/False,
            "codigo": {...},
            "mensaje": "..."
        }
    """

    if not codigo:
        return {
            "valido": False,
            "codigo": None,
            "mensaje": "Debes ingresar un código."
        }

    codigo = codigo.strip().upper()

    respuesta = (
        _cliente()
        .table("codigos_promocionales")
        .select("*")
        .eq("codigo", codigo)
        .limit(1)
        .execute()
    )

    if not respuesta.data:

        return {
            "valido": False,
            "codigo": None,
            "mensaje": "El código promocional no existe."
        }

    promo = respuesta.data[0]

    # --------------------------------------------------------
    # ESTATUS
    # --------------------------------------------------------

    if promo.get("estatus") != "ACTIVO":

        return {
            "valido": False,
            "codigo": promo,
            "mensaje": "El código promocional no está activo."
        }

    ahora = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # FECHA INICIO
    # --------------------------------------------------------

    fecha_inicio = promo.get("fecha_inicio")

    if fecha_inicio:

        fecha_inicio_dt = _convertir_fecha(fecha_inicio)

        if fecha_inicio_dt and ahora < fecha_inicio_dt:

            return {
                "valido": False,
                "codigo": promo,
                "mensaje": "El código todavía no está vigente."
            }

    # --------------------------------------------------------
    # FECHA FIN
    # --------------------------------------------------------

    fecha_fin = promo.get("fecha_fin")

    if fecha_fin:

        fecha_fin_dt = _convertir_fecha(fecha_fin)

        if fecha_fin_dt and ahora > fecha_fin_dt:

            return {
                "valido": False,
                "codigo": promo,
                "mensaje": "El código promocional ha expirado."
            }

    # --------------------------------------------------------
    # LÍMITE DE USOS
    # --------------------------------------------------------

    limite = promo.get("limite_usos", 0)
    usos = promo.get("usos_actuales", 0)

    # 0 significa sin límite.
    if limite and usos >= limite:

        return {
            "valido": False,
            "codigo": promo,
            "mensaje": "El código alcanzó su límite de usos."
        }

    return {
        "valido": True,
        "codigo": promo,
        "mensaje": "Código promocional válido."
    }


# ============================================================
# REGISTRAR USO DE PROMOCIÓN
# ============================================================

def registrar_uso_promocion(codigo: str):
    """
    Incrementa el contador de usos de un código promocional.

    Antes de incrementar vuelve a validar el código para evitar
    utilizar códigos inactivos o expirados.
    """

    validacion = validar_codigo_promocional(codigo)

    if not validacion["valido"]:
        raise ValueError(
            validacion["mensaje"]
        )

    promo = validacion["codigo"]

    nuevos_usos = (
        int(promo.get("usos_actuales", 0)) + 1
    )

    respuesta = (
        _cliente()
        .table("codigos_promocionales")
        .update(
            {
                "usos_actuales": nuevos_usos,
                "fecha_actualizacion":
                    datetime.now(timezone.utc).isoformat()
            }
        )
        .eq("id", promo["id"])
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError(
            "No fue posible registrar el uso del código."
        )

    return respuesta.data[0]


# ============================================================
# OBTENER CONFIGURACIÓN
# ============================================================

def obtener_configuracion(clave: str, default=None):
    """
    Obtiene una configuración por su clave.

    Ejemplo:

        obtener_configuracion("UMA_2026", "117.31")
    """

    respuesta = (
        _cliente()
        .table("configuraciones")
        .select("valor")
        .eq("clave", clave)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        return default

    return respuesta.data[0].get("valor", default)


# ============================================================
# OBTENER UMA
# ============================================================

def obtener_uma():
    """
    Devuelve la UMA configurada para el sistema.
    """

    valor = obtener_configuracion(
        "UMA_2026",
        "117.31"
    )

    try:
        return float(valor)
    except (TypeError, ValueError):

        raise ValueError(
            "El valor de UMA configurado no es numérico."
        )


# ============================================================
# OBTENER PRECIO DEL REPORTE
# ============================================================

def obtener_precio_reporte():
    """
    Devuelve el precio actual del reporte.
    """

    valor = obtener_configuracion(
        "PRECIO_REPORTE",
        "249"
    )

    try:
        return float(valor)
    except (TypeError, ValueError):

        raise ValueError(
            "El precio del reporte no es numérico."
        )


# ============================================================
# ACTUALIZAR CONFIGURACIÓN
# ============================================================

def actualizar_configuracion(
    clave: str,
    valor,
    descripcion: str = None
):
    """
    Crea o actualiza una configuración.
    """

    datos = {
        "clave": clave,
        "valor": str(valor),
        "fecha_actualizacion":
            datetime.now(timezone.utc).isoformat()
    }

    if descripcion is not None:
        datos["descripcion"] = descripcion

    respuesta = (
        _cliente()
        .table("configuraciones")
        .upsert(
            datos,
            on_conflict="clave"
        )
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError(
            "No fue posible actualizar la configuración."
        )

    return respuesta.data[0]


# ============================================================
# ACTUALIZAR UMA
# ============================================================

def actualizar_uma(valor_uma: float):
    """
    Actualiza la UMA utilizada por el sistema.
    """

    if valor_uma <= 0:
        raise ValueError(
            "La UMA debe ser mayor que cero."
        )

    return actualizar_configuracion(
        "UMA_2026",
        round(float(valor_uma), 2),
        "Valor de la UMA utilizado por Pensión 40"
    )


# ============================================================
# CREAR PROMOCIÓN
# ============================================================

def crear_codigo_promocional(
    codigo: str,
    fecha_inicio=None,
    fecha_fin=None,
    limite_usos: int = 0,
    estatus: str = "ACTIVO"
):
    """
    Crea un nuevo código promocional.
    """

    if not codigo or not codigo.strip():
        raise ValueError(
            "El código promocional es obligatorio."
        )

    codigo = codigo.strip().upper()

    estatus = estatus.upper()

    if estatus not in ("ACTIVO", "INACTIVO"):
        raise ValueError(
            "El estatus debe ser ACTIVO o INACTIVO."
        )

    if limite_usos < 0:
        raise ValueError(
            "El límite de usos no puede ser negativo."
        )

    datos = {
        "codigo": codigo,
        "estatus": estatus,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "limite_usos": int(limite_usos),
        "usos_actuales": 0
    }

    respuesta = (
        _cliente()
        .table("codigos_promocionales")
        .insert(datos)
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError(
            "No fue posible crear la promoción."
        )

    return respuesta.data[0]


# ============================================================
# ACTIVAR / DESACTIVAR PROMOCIÓN
# ============================================================

def cambiar_estatus_promocion(
    codigo: str,
    estatus: str
):
    """
    Cambia el estado de una promoción.
    """

    codigo = codigo.strip().upper()
    estatus = estatus.strip().upper()

    if estatus not in ("ACTIVO", "INACTIVO"):
        raise ValueError(
            "Estatus inválido."
        )

    respuesta = (
        _cliente()
        .table("codigos_promocionales")
        .update(
            {
                "estatus": estatus,
                "fecha_actualizacion":
                    datetime.now(timezone.utc).isoformat()
            }
        )
        .eq("codigo", codigo)
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError(
            "No se encontró el código promocional."
        )

    return respuesta.data[0]


# ============================================================
# LISTAR PROMOCIONES
# ============================================================

def obtener_promociones():
    """
    Obtiene todas las promociones.
    """

    respuesta = (
        _cliente()
        .table("codigos_promocionales")
        .select("*")
        .order(
            "fecha_creacion",
            desc=True
        )
        .execute()
    )

    return respuesta.data or []


# ============================================================
# AUTENTICACIÓN ADMINISTRATIVA
# ============================================================

def _hash_password(password: str) -> str:
    """
    Genera SHA-256 para comparación de contraseñas.

    La contraseña almacenada en configuraciones puede ser:

        sha256:HASH

    """

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verificar_password_admin(password: str) -> bool:
    """
    Verifica la contraseña administrativa.

    Busca ADMIN_PASSWORD_HASH en configuraciones.

    Por seguridad no devuelve nunca la contraseña.
    """

    if not password:
        return False

    hash_guardado = obtener_configuracion(
        "ADMIN_PASSWORD_HASH",
        None
    )

    if not hash_guardado:
        return False

    hash_guardado = str(hash_guardado)

    if hash_guardado.startswith("sha256:"):
        hash_guardado = hash_guardado[7:]

    hash_ingresado = _hash_password(password)

    return hmac.compare_digest(
        hash_ingresado,
        hash_guardado
    )


# ============================================================
# CREAR / CAMBIAR CONTRASEÑA ADMIN
# ============================================================

def establecer_password_admin(password: str):
    """
    Guarda la contraseña administrativa como SHA-256.

    IMPORTANTE:
    Esta función será utilizada únicamente desde el entorno
    administrativo, nunca directamente desde la interfaz pública.
    """

    if not password or len(password) < 10:

        raise ValueError(
            "La contraseña administrativa debe tener "
            "al menos 10 caracteres."
        )

    hash_password = _hash_password(password)

    return actualizar_configuracion(
        "ADMIN_PASSWORD_HASH",
        f"sha256:{hash_password}",
        "Hash de la contraseña administrativa"
    )


# ============================================================
# CONVERSIÓN DE FECHAS
# ============================================================

def _convertir_fecha(valor):
    """
    Convierte fechas ISO de Supabase a datetime UTC.
    """

    if not valor:
        return None

    if isinstance(valor, datetime):

        if valor.tzinfo is None:
            return valor.replace(
                tzinfo=timezone.utc
            )

        return valor

    try:

        texto = str(valor)

        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"

        resultado = datetime.fromisoformat(texto)

        if resultado.tzinfo is None:
            resultado = resultado.replace(
                tzinfo=timezone.utc
            )

        return resultado

    except (ValueError, TypeError):

        return None


# ============================================================
# PRUEBA DE CONEXIÓN
# ============================================================

def probar_conexion():
    """
    Comprueba que Pensión 40 puede comunicarse con Supabase.

    Retorna True si la conexión funciona.
    """

    try:

        _cliente() \
            .table("configuraciones") \
            .select("clave") \
            .limit(1) \
            .execute()

        return True

    except Exception:

        return False
