# ============================================================
# PENSION 40
# app.py
# Aplicación principal Streamlit
# ============================================================

import streamlit as st

# ============================================================
# MÓDULOS DEL PROYECTO
# ============================================================

from base_datos import (
    validar_codigo_promocional,
    registrar_uso_promocion,
    obtener_uma,
    obtener_precio_reporte,
    actualizar_uma,
    verificar_password_admin,
    crear_codigo_promocional,
    cambiar_estatus_promocion,
    obtener_promociones,
)

# ============================================================
# EXTRACTOR
# ============================================================

try:
    from extractor import (
        analizar_pdf_streamlit,
        Ley97Error,
        SemanasInsuficientesError,
        ExtractorPensionError,
    )
    EXTRACTOR_DISPONIBLE = True

except ImportError:
    EXTRACTOR_DISPONIBLE = False


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Pensión 40",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# VARIABLES GENERALES
# ============================================================

NOMBRE_APP = "Pensión 40"
PRECIO_REPORTE_DEFAULT = 249


# ============================================================
# SESSION STATE
# ============================================================

valores_iniciales = {
    "admin_autenticado": False,
    "pdf": None,
    "datos_cliente": {},
    "resultado_extraccion": None,
    "resultado_calculo": None,
    "promo_validada": False,
    "codigo_promo": "",
    "pago_confirmado": False,
    "reporte_generado": False,
    "prospecto_id": None,
    "promo_uso_registrado": False,
}

for clave, valor in valores_iniciales.items():

    if clave not in st.session_state:
        st.session_state[clave] = valor


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>

    .main .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .titulo {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitulo {
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .card {
        padding: 1.4rem;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 1rem;
    }

    .precio {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
    }

    .centrado {
        text-align: center;
    }

    .stButton > button {
        width: 100%;
        min-height: 3rem;
        border-radius: 10px;
        font-weight: 700;
    }

    .footer {
        text-align: center;
        font-size: 0.8rem;
        opacity: 0.65;
        margin-top: 3rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ENCABEZADO
# ============================================================

def mostrar_encabezado():

    st.markdown(
        '<div class="titulo">Pensión 40</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="subtitulo">
        Simulador financiero de pensión bajo Ley 73 del IMSS
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PRESENTACIÓN
# ============================================================

def mostrar_presentacion():

    st.markdown(
        """
        <div class="card">

        <h3>📊 Calcula el potencial de tu pensión</h3>

        Analizamos tu Constancia de Semanas Cotizadas del IMSS
        para determinar si perteneces al régimen de Ley 73 y
        preparar tu escenario financiero.

        <br><br>

        <strong>Necesitas:</strong>

        <br><br>

        • Constancia de Semanas Cotizadas del IMSS<br>
        • Nombre completo<br>
        • Correo electrónico<br>
        • WhatsApp

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DATOS DEL CLIENTE
# ============================================================

def capturar_datos():

    st.subheader("1. Tus datos")

    nombre = st.text_input(
        "Nombre completo",
        placeholder="Nombre y apellidos",
        key="nombre_cliente",
    )

    correo = st.text_input(
        "Correo electrónico",
        placeholder="correo@ejemplo.com",
        key="correo_cliente",
    )

    telefono = st.text_input(
        "WhatsApp",
        placeholder="10 dígitos",
        key="telefono_cliente",
    )

    st.session_state.datos_cliente = {
        "nombre": nombre.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip(),
    }


# ============================================================
# CARGA DEL PDF
# ============================================================

def cargar_pdf():

    st.subheader("2. Sube tu Constancia de Semanas Cotizadas")

    st.write(
        "El documento debe ser el PDF emitido por el IMSS."
    )

    archivo = st.file_uploader(
        "Seleccionar PDF",
        type=["pdf"],
        accept_multiple_files=False,
        key="archivo_imss",
    )

    if archivo:

        st.session_state.pdf = archivo

        st.success(
            f"PDF recibido: {archivo.name}"
        )

        st.caption(
            f"Tamaño: {archivo.size / 1024:.1f} KB"
        )


# ============================================================
# VALIDACIÓN DE DATOS
# ============================================================

def validar_datos():

    errores = []

    datos = st.session_state.datos_cliente

    if not datos.get("nombre"):
        errores.append(
            "Ingresa tu nombre completo."
        )

    if not datos.get("correo"):
        errores.append(
            "Ingresa tu correo electrónico."
        )

    if not datos.get("telefono"):
        errores.append(
            "Ingresa tu WhatsApp."
        )

    if st.session_state.pdf is None:
        errores.append(
            "Debes subir tu Constancia de Semanas Cotizadas."
        )

    return errores


# ============================================================
# PROCESAR INFORMACIÓN
# ============================================================

def procesar_informacion():

    errores = validar_datos()

    if errores:

        for error in errores:
            st.error(error)

        return

    if not EXTRACTOR_DISPONIBLE:

        st.error(
            "El módulo extractor.py todavía no está "
            "disponible correctamente."
        )

        return

    with st.spinner(
        "Analizando tu información del IMSS..."
    ):

        try:

            resultado = analizar_pdf_streamlit(
                st.session_state.pdf
            )

            st.session_state.resultado_extraccion = resultado

        except Ley97Error as error:

            st.session_state.resultado_extraccion = None

            st.error(
                "❌ Este documento corresponde al régimen "
                "de Ley 97 del IMSS."
            )

            st.warning(str(error))

            return

        except SemanasInsuficientesError as error:

            st.session_state.resultado_extraccion = None

            st.warning(str(error))

            return

        except ExtractorPensionError as error:

            st.session_state.resultado_extraccion = None

            st.error(
                f"No fue posible analizar el documento: {error}"
            )

            return

        except Exception as error:

            st.session_state.resultado_extraccion = None

            st.error(
                "Ocurrió un error al procesar el PDF."
            )

            st.exception(error)

            return

    st.success(
        "✅ Tu documento fue analizado correctamente."
    )

    resultado = st.session_state.resultado_extraccion

    if not resultado:
        return

    # ========================================================
    # MOSTRAR RESULTADOS
    # ========================================================

    st.subheader("Resultado preliminar")

    col1, col2 = st.columns(2)

    with col1:

        semanas = resultado.get(
            "semanas_cotizadas",
            "No disponible",
        )

        st.metric(
            "Semanas cotizadas",
            semanas,
        )

    with col2:

        sbc = resultado.get(
            "sbc_promedio",
            None,
        )

        if sbc is not None:

            st.metric(
                "SBC promedio",
                f"${float(sbc):,.2f}",
            )

        else:

            st.metric(
                "SBC promedio",
                "No disponible",
            )

    # ========================================================
    # PRIMERA COTIZACIÓN
    # ========================================================

    fecha = resultado.get(
        "primera_fecha_cotizacion"
    )

    if fecha:

        if hasattr(fecha, "strftime"):

            fecha_texto = fecha.strftime(
                "%d/%m/%Y"
            )

        else:

            fecha_texto = str(fecha)

        st.write(
            f"**Primera cotización:** {fecha_texto}"
        )

    # ========================================================
    # RÉGIMEN
    # ========================================================

    ley = resultado.get(
        "ley",
        "Ley 73",
    )

    if ley == "Ley 97":

        st.error(
            "Este documento corresponde a Ley 97."
        )

        return

    st.success(
        "✅ El documento cumple con el criterio "
        "de Ley 73."
    )

    # ========================================================
    # SEMANAS
    # ========================================================

    validacion = resultado.get(
        "validacion_semanas",
        {},
    )

    if validacion:

        mensaje = validacion.get(
            "mensaje",
            "",
        )

        if mensaje:
            st.info(mensaje)

    # ========================================================
    # ÚLTIMAS 250 SEMANAS
    # ========================================================

    ultimas = resultado.get(
        "ultimas_250_semanas",
        {},
    )

    dias = ultimas.get(
        "dias_acumulados",
        0,
    )

    st.write(
        f"**Días utilizados para el promedio:** "
        f"{dias:,} de 1,750"
    )

    if not ultimas.get(
        "completo",
        False,
    ):

        st.warning(
            "No se pudieron identificar 1,750 días "
            "completos en el historial detectado. "
            "El resultado deberá revisarse antes "
            "de utilizarlo para una simulación."
        )


# ============================================================
# RESULTADO
# ============================================================

def mostrar_resultado():

    if not st.session_state.resultado_extraccion:
        return

    st.divider()

    st.subheader("3. Resultado de tu análisis")

    resultado = st.session_state.resultado_extraccion

    semanas = resultado.get(
        "semanas_cotizadas",
        "No disponible",
    )

    sbc = resultado.get(
        "sbc_promedio",
        None,
    )

    st.markdown(
        """
        <div class="card">

        <h3>🎯 Tu análisis preliminar</h3>

        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Semanas cotizadas",
            semanas,
        )

    with col2:

        if sbc is not None:

            st.metric(
                "SBC promedio",
                f"${float(sbc):,.2f}",
            )

        else:

            st.metric(
                "SBC promedio",
                "No disponible",
            )

    st.caption(
        "El resultado es una estimación preliminar. "
        "El cálculo financiero completo se generará "
        "con el motor de simulación."
    )


# ============================================================
# PROMOCIÓN
# ============================================================

def validar_promocion():

    st.subheader("4. ¿Tienes un código promocional?")

    st.write(
        "Si recibiste un código promocional de Pensión 40, "
        "puedes ingresarlo aquí."
    )

    codigo = st.text_input(
        "Código promocional",
        placeholder="Ejemplo: P40-PRUEBA",
        key="codigo_promocional",
    )

    if st.button(
        "Validar código promocional",
        key="btn_validar_promo",
    ):

        if not codigo.strip():

            st.warning(
                "Ingresa un código promocional."
            )

            return

        codigo = codigo.strip().upper()

        with st.spinner(
            "Validando código promocional..."
        ):

            try:

                resultado = validar_codigo_promocional(
                    codigo
                )

            except Exception as error:

                st.error(
                    "No fue posible comunicarse con "
                    "la base de datos de Supabase."
                )

                st.exception(error)

                return

        if resultado.get("valido"):

            st.session_state.codigo_promo = codigo

            st.session_state.promo_validada = True

            st.success(
                "🎉 ¡Código promocional válido!"
            )

            st.info(
                "Tu reporte financiero completo "
                "ha sido desbloqueado."
            )

            st.rerun()

        else:

            st.session_state.codigo_promo = ""

            st.session_state.promo_validada = False

            st.error(
                resultado.get(
                    "mensaje",
                    "El código promocional no es válido.",
                )
            )


# ============================================================
# REGISTRAR USO DEL CÓDIGO
# ============================================================

def registrar_uso_promo():

    if not st.session_state.promo_validada:
        return True

    if st.session_state.promo_uso_registrado:
        return True

    codigo = st.session_state.codigo_promo

    if not codigo:
        return False

    try:

        registrar_uso_promocion(
            codigo
        )

        st.session_state.promo_uso_registrado = True

        return True

    except Exception as error:

        st.error(
            "El código fue validado, pero no fue posible "
            "registrar su uso en Supabase."
        )

        st.exception(error)

        return False


# ============================================================
# ACCESO AL REPORTE
# ============================================================

def mostrar_acceso_reporte():

    if not st.session_state.resultado_extraccion:
        return

    st.divider()

    st.subheader(
        "5. Reporte financiero completo"
    )

    st.write(
        "Obtén tu proyección financiera completa "
        "de Modalidad 40."
    )

    # ========================================================
    # PROMOCIÓN VÁLIDA
    # ========================================================

    if st.session_state.promo_validada:

        st.success(
            "🎉 Código promocional válido. "
            "Tu reporte está desbloqueado."
        )

        mostrar_descarga_reporte()

        return

    # ========================================================
    # PRECIO
    # ========================================================

    try:

        precio = obtener_precio_reporte()

    except Exception:

        precio = PRECIO_REPORTE_DEFAULT

    st.markdown(
        f"""
        <div class="card">

        <div class="precio">
        ${precio:,.0f} MXN
        </div>

        <div class="centrado">
        Reporte financiero completo
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "El reporte incluye:"
    )

    st.markdown(
        """
        ✓ Proyección de pensión<br>
        ✓ Análisis de Modalidad 40<br>
        ✓ Inversión requerida<br>
        ✓ Proyección mes a mes<br>
        ✓ Costo acumulado<br>
        ✓ Retorno de inversión (ROI)<br>
        ✓ Escenarios de retiro
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # PAGO
    # ========================================================

    if not st.session_state.pago_confirmado:

        if st.button(
            f"💳 Obtener reporte por ${precio:,.0f} MXN",
            type="primary",
            key="btn_pago",
        ):

            st.info(
                "La pasarela de pago se conectará "
                "en la siguiente etapa."
            )

    else:

        mostrar_descarga_reporte()


# ============================================================
# DESCARGA DEL REPORTE
# ============================================================

def mostrar_descarga_reporte():

    st.success(
        "Tu reporte financiero está desbloqueado."
    )

    # ========================================================
    # REGISTRAR USO DEL PROMO
    # ========================================================

    if st.session_state.promo_validada:

        registrar_uso_promo()

    # ========================================================
    # PDF
    # ========================================================

    st.info(
        "El PDF ejecutivo será generado por correo.py "
        "cuando conectemos el motor de reportes."
    )

    st.button(
        "📥 Descargar reporte PDF",
        disabled=True,
        key="btn_descarga_pdf",
    )


# ============================================================
# PANEL ADMINISTRATIVO
# ============================================================

def panel_administrador():

    st.divider()

    with st.expander(
        "⚙️ Administración"
    ):

        # ====================================================
        # LOGIN
        # ====================================================

        if not st.session_state.admin_autenticado:

            st.subheader(
                "Acceso administrativo"
            )

            password = st.text_input(
                "Contraseña",
                type="password",
                key="password_admin",
            )

            if st.button(
                "🔐 Ingresar",
                key="btn_admin_login",
            ):

                try:

                    correcto = verificar_password_admin(
                        password
                    )

                except Exception as error:

                    st.error(
                        "No fue posible verificar "
                        "la contraseña en Supabase."
                    )

                    st.exception(error)

                    return

                if correcto:

                    st.session_state.admin_autenticado = True

                    st.success(
                        "Administrador autenticado."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Contraseña incorrecta."
                    )

            return

        # ====================================================
        # PANEL
        # ====================================================

        st.success(
            "Administrador autenticado."
        )

        st.subheader(
            "⚙️ Configuración de Pensión 40"
        )

        # ====================================================
        # UMA
        # ====================================================

        try:

            uma_actual = obtener_uma()

        except Exception:

            uma_actual = 117.31

        uma_nueva = st.number_input(
            "Valor actual de UMA",
            min_value=0.01,
            value=float(uma_actual),
            step=0.01,
            format="%.2f",
            key="uma_admin",
        )

        if st.button(
            "Guardar UMA",
            key="btn_guardar_uma",
        ):

            try:

                actualizar_uma(
                    uma_nueva
                )

                st.success(
                    "✅ UMA actualizada correctamente "
                    "en Supabase."
                )

            except Exception as error:

                st.error(
                    "No fue posible actualizar la UMA."
                )

                st.exception(error)

        # ====================================================
        # PROMOCIONES
        # ====================================================

        st.divider()

        st.subheader(
            "🎟️ Crear promoción"
        )

        codigo = st.text_input(
            "Nuevo código",
            placeholder="Ej. P40-FACEBOOK-AGOSTO",
            key="nuevo_codigo",
        )

        col1, col2 = st.columns(2)

        with col1:

            activo = st.checkbox(
                "Código ACTIVO",
                value=True,
                key="nuevo_codigo_activo",
            )

        with col2:

            limite = st.number_input(
                "Límite de usos",
                min_value=0,
                value=100,
                step=1,
                key="limite_codigo",
            )

        if st.button(
            "➕ Crear promoción",
            key="btn_crear_promo",
        ):

            if not codigo.strip():

                st.warning(
                    "Ingresa un código."
                )

            else:

                try:

                    estatus = (
                        "ACTIVO"
                        if activo
                        else "INACTIVO"
                    )

                    crear_codigo_promocional(
                        codigo=codigo,
                        limite_usos=limite,
                        estatus=estatus,
                    )

                    st.success(
                        f"✅ Promoción {codigo.upper()} "
                        "creada correctamente."
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        "No fue posible crear la promoción."
                    )

                    st.exception(error)

        # ====================================================
        # PROMOCIONES EXISTENTES
        # ====================================================

        st.divider()

        st.subheader(
            "📋 Promociones existentes"
        )

        try:

            promociones = obtener_promociones()

        except Exception as error:

            st.error(
                "No fue posible obtener las promociones "
                "desde Supabase."
            )

            st.exception(error)

            promociones = []

        if not promociones:

            st.info(
                "No existen promociones registradas."
            )

        else:

            for promo in promociones:

                codigo_existente = promo.get(
                    "codigo",
                    "",
                )

                estatus_actual = promo.get(
                    "estatus",
                    "INACTIVO",
                )

                usos = promo.get(
                    "usos_actuales",
                    0,
                )

                limite_usos = promo.get(
                    "limite_usos",
                    0,
                )

                col1, col2, col3 = st.columns(
                    [2, 1, 1]
                )

                with col1:

                    st.write(
                        f"**{codigo_existente}**"
                    )

                    st.caption(
                        f"Usos: {usos} / "
                        f"{limite_usos if limite_usos else '∞'}"
                    )

                with col2:

                    st.write(
                        estatus_actual
                    )

                with col3:

                    if estatus_actual == "ACTIVO":

                        if st.button(
                            "Desactivar",
                            key=f"desactivar_{codigo_existente}",
                        ):

                            try:

                                cambiar_estatus_promocion(
                                    codigo_existente,
                                    "INACTIVO",
                                )

                                st.success(
                                    "Código desactivado."
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    "No fue posible "
                                    "desactivar el código."
                                )

                                st.exception(error)

                    else:

                        if st.button(
                            "Activar",
                            key=f"activar_{codigo_existente}",
                        ):

                            try:

                                cambiar_estatus_promocion(
                                    codigo_existente,
                                    "ACTIVO",
                                )

                                st.success(
                                    "Código activado."
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    "No fue posible "
                                    "activar el código."
                                )

                                st.exception(error)

        # ====================================================
        # CERRAR SESIÓN
        # ====================================================

        st.divider()

        if st.button(
            "Cerrar sesión administrativa",
            key="btn_admin_logout",
        ):

            st.session_state.admin_autenticado = False

            st.rerun()


# ============================================================
# AVISO LEGAL
# ============================================================

def mostrar_aviso_legal():

    st.markdown(
        """
        <div class="footer">

        Pensión 40 · Simulador financiero Ley 73 IMSS

        <br><br>

        Las proyecciones generadas por este sistema son
        estimaciones financieras y no constituyen una resolución
        oficial del Instituto Mexicano del Seguro Social.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    mostrar_encabezado()

    mostrar_presentacion()

    capturar_datos()

    cargar_pdf()

    st.divider()

    if st.button(
        "🚀 Calcular mi potencial de pensión",
        type="primary",
        key="btn_calcular",
    ):

        procesar_informacion()

    mostrar_resultado()

    if st.session_state.resultado_extraccion:

        validar_promocion()

        mostrar_acceso_reporte()

    mostrar_aviso_legal()

    panel_administrador()


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    main()
