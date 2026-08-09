
# ============================================================
# PENSION 40
# Aplicación principal Streamlit
# ============================================================
#
# Este archivo controla ÚNICAMENTE:
#
# - Interfaz
# - Captura de datos
# - Carga del PDF
# - Flujo de usuario
# - Panel administrativo
#
# La lógica estará separada en:
#
# extractor.py
# calculador.py
# base_datos.py
# correo.py
#
# ============================================================

import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Pensión 40",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# VARIABLES GENERALES
# ============================================================

PRECIO_REPORTE = 249
NOMBRE_APP = "Pensión 40"


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
    unsafe_allow_html=True
)


# ============================================================
# ENCABEZADO
# ============================================================

def mostrar_encabezado():

    st.markdown(
        '<div class="titulo">Pensión 40</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="subtitulo">
        Simulador financiero de pensión bajo Ley 73 del IMSS
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# PRESENTACIÓN
# ============================================================

def mostrar_presentacion():

    st.markdown(
        """
        <div class="card">

        ### 📊 Calcula el potencial de tu pensión

        Analizamos tu Constancia de Semanas Cotizadas del IMSS
        para determinar si perteneces al régimen de Ley 73 y
        calcular tu escenario de pensión.

        <br>

        <strong>Necesitas:</strong>

        <br><br>

        • Constancia de Semanas Cotizadas del IMSS<br>
        • Nombre completo<br>
        • Correo electrónico<br>
        • WhatsApp

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATOS DEL CLIENTE
# ============================================================

def capturar_datos():

    st.subheader("1. Tus datos")

    nombre = st.text_input(
        "Nombre completo",
        placeholder="Nombre y apellidos",
        key="nombre_cliente"
    )

    correo = st.text_input(
        "Correo electrónico",
        placeholder="correo@ejemplo.com",
        key="correo_cliente"
    )

    telefono = st.text_input(
        "WhatsApp",
        placeholder="10 dígitos",
        key="telefono_cliente"
    )

    st.session_state.datos_cliente = {
        "nombre": nombre.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip()
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
        key="archivo_imss"
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
        errores.append("Ingresa tu nombre completo.")

    if not datos.get("correo"):
        errores.append("Ingresa tu correo electrónico.")

    if not datos.get("telefono"):
        errores.append("Ingresa tu WhatsApp.")

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

    with st.spinner(
        "Analizando tu información del IMSS..."
    ):

        # ====================================================
        # AQUÍ CONECTAREMOS:
        #
        # extractor.py
        #
        # resultado = analizar_pdf(
        #     st.session_state.pdf
        # )
        #
        # ====================================================

        st.session_state.resultado_extraccion = {
            "procesado": True
        }

    st.success(
        "Tu documento fue recibido y está listo para análisis."
    )

    st.info(
        "El motor de extracción se conectará con extractor.py."
    )


# ============================================================
# RESULTADO INICIAL
# ============================================================

def mostrar_resultado():

    if not st.session_state.resultado_extraccion:
        return

    st.divider()

    st.subheader("3. Resultado de tu análisis")

    st.markdown(
        """
        <div class="card">

        ### 🎯 Análisis inicial

        Tu información fue procesada correctamente.

        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Los datos reales de semanas, Ley 73 y SBC promedio "
        "serán proporcionados por extractor.py."
    )


# ============================================================
# PROMOCIÓN
# ============================================================

def procesar_informacion():

    errores = validar_datos()

    if errores:

        for error in errores:
            st.error(error)

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
                "Ocurrió un error inesperado al procesar "
                "el PDF."
            )

            st.exception(error)

            return

    st.success(
        "✅ Tu documento fue analizado correctamente."
    )

    resultado = st.session_state.resultado_extraccion

    if resultado:

        st.subheader("Resultado preliminar")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Semanas cotizadas",
                resultado.get(
                    "semanas_cotizadas",
                    "No disponible"
                )
            )

        with col2:

            sbc = resultado.get(
                "sbc_promedio"
            )

            if sbc is not None:

                st.metric(
                    "SBC promedio",
                    f"${sbc:,.2f}"
                )

            else:

                st.metric(
                    "SBC promedio",
                    "No disponible"
                )

        fecha = resultado.get(
            "primera_fecha_cotizacion"
        )

        if fecha:

            st.write(
                f"**Primera cotización:** "
                f"{fecha.strftime('%d/%m/%Y')}"
            )

        st.success(
            "✅ El documento cumple con el criterio "
            "de Ley 73."
        )

        validacion = resultado.get(
            "validacion_semanas",
            {}
        )

        if validacion:

            st.info(
                validacion.get(
                    "mensaje",
                    ""
                )
            )

        ultimas = resultado.get(
            "ultimas_250_semanas",
            {}
        )

        dias = ultimas.get(
            "dias_acumulados",
            0
        )

        st.write(
            f"**Días utilizados para el promedio:** "
            f"{dias:,} de 1,750"
        )

        if not ultimas.get(
            "completo",
            False
        ):

            st.warning(
                "No se pudieron identificar "
                "1,750 días completos en el historial "
                "detectado. El resultado debe revisarse "
                "antes de utilizarlo para una simulación."
            )
# ============================================================
# ACCESO AL REPORTE
# ============================================================
def validar_promocion():

    st.subheader("4. ¿Tienes un código promocional?")

    st.write(
        "Si recibiste un código promocional de Pensión 40, "
        "puedes ingresarlo aquí."
    )

    codigo = st.text_input(
        "Código promocional",
        placeholder="Ejemplo: P40-FACEBOOK",
        key="codigo_promocional"
    )

    if st.button(
        "Validar código promocional",
        key="btn_validar_promo"
    ):

        if not codigo.strip():

            st.warning(
                "Ingresa un código promocional."
            )

            return

        st.session_state.codigo_promo = (
            codigo.strip().upper()
        )

        st.info(
            "La validación del código promocional "
            "se conectará con Supabase."
        )
def mostrar_acceso_reporte():

    if not st.session_state.resultado_extraccion:
        return

    st.divider()

    st.subheader("5. Reporte financiero completo")

    st.write(
        "Obtén tu proyección financiera completa de "
        "Modalidad 40."
    )

    # ========================================================
    # SI PROMOCIÓN ES VÁLIDA
    # ========================================================

    if st.session_state.promo_validada:

        st.success(
            "🎉 Código promocional válido. "
            "Tu reporte está desbloqueado."
        )

        mostrar_descarga_reporte()

        return

    # ========================================================
    # SI NO HAY PROMOCIÓN / PAGO
    # ========================================================

    st.markdown(
        f"""
        <div class="card">

        <div class="precio">
        ${PRECIO_REPORTE} MXN
        </div>

        <div class="centrado">
        Reporte financiero completo
        </div>

        </div>
        """,
        unsafe_allow_html=True
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
        unsafe_allow_html=True
    )

    # ========================================================
    # PAGO
    # ========================================================

    if not st.session_state.pago_confirmado:

        if st.button(
            f"💳 Obtener reporte por ${PRECIO_REPORTE} MXN",
            type="primary",
            key="btn_pago"
        ):

            # =================================================
            # AQUÍ CONECTAREMOS STRIPE / MERCADO PAGO
            # =================================================

            st.info(
                "La pasarela de pago se conectará en la "
                "siguiente etapa."
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
    # AQUÍ CONECTAREMOS:
    #
    # correo.py
    #
    # generar_pdf(...)
    #
    # ========================================================

    st.info(
        "El PDF ejecutivo será generado por correo.py."
    )

    # Cuando correo.py genere el archivo, aquí tendremos:
    #
    # st.download_button(
    #     "📥 Descargar reporte PDF",
    #     data=pdf,
    #     file_name="Reporte_Pension40.pdf",
    #     mime="application/pdf"
    # )

    st.button(
        "📥 Descargar reporte PDF",
        disabled=True,
        key="btn_descarga_pdf"
    )


# ============================================================
# PANEL ADMINISTRATIVO
# ============================================================

def panel_administrador():

    st.divider()

    with st.expander("⚙️ Administración"):

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
                key="password_admin"
            )

            if st.button(
                "🔐 Ingresar",
                key="btn_admin_login"
            ):

                # =================================================
                # AQUÍ CONECTAREMOS:
                #
                # base_datos.verificar_admin(password)
                #
                # La contraseña estará almacenada en:
                #
                # Supabase → configuraciones
                #
                # NO en app.py
                # =================================================

                st.warning(
                    "La autenticación administrativa se "
                    "conectará con Supabase."
                )

        # ====================================================
        # PANEL
        # ====================================================

        else:

            st.success(
                "Administrador autenticado."
            )

            st.subheader(
                "⚙️ Configuración de Pensión 40"
            )

            # =================================================
            # UMA
            # =================================================

            st.number_input(
                "Valor actual de UMA",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="uma_admin"
            )

            if st.button(
                "Guardar UMA",
                key="btn_guardar_uma"
            ):

                # =============================================
                # base_datos.actualizar_configuracion()
                # =============================================

                st.success(
                    "La UMA se guardará en Supabase."
                )

            # =================================================
            # PROMOCIONES
            # =================================================

            st.divider()

            st.subheader(
                "🎟️ Promociones"
            )

            st.write(
                "Desde aquí podrás crear y administrar "
                "códigos promocionales."
            )

            codigo = st.text_input(
                "Nuevo código",
                placeholder="Ej. P40-FACEBOOK-AGOSTO",
                key="nuevo_codigo"
            )

            col1, col2 = st.columns(2)

            with col1:

                activo = st.checkbox(
                    "Código ACTIVO",
                    value=True,
                    key="nuevo_codigo_activo"
                )

            with col2:

                limite = st.number_input(
                    "Límite de usos",
                    min_value=0,
                    value=100,
                    step=1,
                    key="limite_codigo"
                )

            if st.button(
                "➕ Crear promoción",
                key="btn_crear_promo"
            ):

                # =============================================
                # base_datos.crear_codigo_promocional()
                # =============================================

                st.success(
                    "La promoción se guardará en Supabase."
                )

            st.divider()

            st.subheader(
                "📋 Promociones existentes"
            )

            st.info(
                "Aquí aparecerán las promociones almacenadas "
                "en Supabase, con opción para activarlas o "
                "desactivarlas."
            )

            # ================================================
            # base_datos.obtener_promociones()
            # ================================================

            # =================================================
            # CERRAR SESIÓN
            # =================================================

            if st.button(
                "Cerrar sesión administrativa",
                key="btn_admin_logout"
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
        unsafe_allow_html=True
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
        key="btn_calcular"
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
