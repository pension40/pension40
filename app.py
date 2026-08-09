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
# CALCULADOR
# ============================================================

try:
    from calculador import (
        calcular_escenario,
        resumen_escenario,
        CalculadorPensionError,
    )
    CALCULADOR_DISPONIBLE = True

except ImportError:
    CALCULADOR_DISPONIBLE = False


# ============================================================
# GENERADOR DE PDF
# ============================================================

try:
    from reporte_pdf import generar_reporte_pdf
    PDF_DISPONIBLE = True

except ImportError:
    PDF_DISPONIBLE = False


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
    "edad_retiro": 60,
    "tipo_asignacion": "ninguna",
    "meses_m40": 58,
    "pdf_reporte_bytes": None,
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

    :root {
        --azul-oscuro: #0B2545;
        --azul-principal: #134074;
        --azul-medio: #1B6CA8;
        --azul-claro: #E8F1FA;
        --azul-hover: #0F5A8F;
        --verde-ok: #1E8A4C;
        --gris-texto: #3B3B3B;
        --gris-borde: #D9E2EC;
    }

    .main .block-container {
        max-width: 880px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    /* ---------- ENCABEZADO ---------- */

    .header-wrap {
        text-align: center;
        margin-bottom: 1.6rem;
    }

    .titulo {
        text-align: center;
        font-size: 2.6rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }

    .subtitulo {
        text-align: center;
        font-size: 1.05rem;
        color: var(--azul-medio);
        font-weight: 500;
        margin-bottom: 0.4rem;
    }

    .linea-divisora {
        height: 4px;
        width: 90px;
        background: linear-gradient(90deg, var(--azul-medio), var(--azul-oscuro));
        margin: 0.6rem auto 1.8rem auto;
        border-radius: 4px;
    }

    /* ---------- TARJETAS ---------- */

    .card {
        padding: 1.5rem 1.6rem;
        border-radius: 14px;
        border: 1px solid var(--gris-borde);
        background: #FFFFFF;
        box-shadow: 0 2px 10px rgba(11, 37, 69, 0.06);
        margin-bottom: 1.2rem;
    }

    .card h3 {
        color: var(--azul-oscuro);
        margin-top: 0;
    }

    .card-azul {
        padding: 1.5rem 1.6rem;
        border-radius: 14px;
        background: var(--azul-claro);
        border: 1px solid rgba(27, 108, 168, 0.25);
        margin-bottom: 1.2rem;
    }

    /* ---------- PASO / SECCIÓN ---------- */

    .paso-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--azul-oscuro);
        color: white;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        margin-bottom: 0.8rem;
    }

    /* ---------- PRECIO ---------- */

    .precio {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin-bottom: 0.2rem;
    }

    .precio-detalle {
        text-align: center;
        font-size: 0.95rem;
        color: var(--gris-texto);
        opacity: 0.8;
        margin-bottom: 0.6rem;
    }

    .centrado {
        text-align: center;
    }

    /* ---------- LISTA DE BENEFICIOS ---------- */

    .beneficios {
        list-style: none;
        padding-left: 0;
        margin: 0.6rem 0 0.2rem 0;
    }

    .beneficios li {
        padding: 0.35rem 0;
        color: var(--gris-texto);
        font-size: 0.98rem;
    }

    .beneficios li::before {
        content: "✓";
        color: var(--verde-ok);
        font-weight: 800;
        margin-right: 0.6rem;
    }

    /* ---------- BOTONES ---------- */

    .stButton > button {
        width: 100%;
        min-height: 3rem;
        border-radius: 10px;
        font-weight: 700;
        border: none;
        transition: transform 0.05s ease-in-out;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--azul-medio), var(--azul-oscuro));
    }

    div[data-testid="stDownloadButton"] > button {
        width: 100%;
        min-height: 3.2rem;
        border-radius: 10px;
        font-weight: 700;
        background: linear-gradient(90deg, var(--verde-ok), #166B3A);
        color: white;
        border: none;
    }

    /* ---------- BANNER DE DESBLOQUEO ---------- */

    .banner-desbloqueado {
        background: linear-gradient(90deg, #E6F4EA, #EFFAF2);
        border: 1px solid rgba(30, 138, 76, 0.35);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        margin-bottom: 1rem;
    }

    .banner-desbloqueado .icono {
        font-size: 1.8rem;
    }

    .banner-desbloqueado .texto-principal {
        font-weight: 800;
        color: var(--verde-ok);
        font-size: 1.15rem;
        margin: 0.3rem 0 0.1rem 0;
    }

    /* ---------- FOOTER ---------- */

    .footer {
        text-align: center;
        font-size: 0.8rem;
        color: var(--gris-texto);
        opacity: 0.65;
        margin-top: 3rem;
        line-height: 1.5;
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
        """
        <div class="header-wrap">
            <div class="titulo">📊 Pensión 40</div>
            <div class="subtitulo">
                Simulador financiero de pensión bajo Ley 73 del IMSS
            </div>
            <div class="linea-divisora"></div>
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

        <h3>Calcula el potencial de tu pensión</h3>

        Analizamos tu Constancia de Semanas Cotizadas del IMSS
        para determinar si perteneces al régimen de Ley 73 y
        preparar tu escenario financiero de Modalidad 40.

        <p><strong>Necesitas:</strong></p>

        <ul class="beneficios">
            <li>Constancia de Semanas Cotizadas del IMSS</li>
            <li>Nombre completo</li>
            <li>Correo electrónico</li>
            <li>WhatsApp</li>
        </ul>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DATOS DEL CLIENTE
# ============================================================

def capturar_datos():

    st.markdown(
        '<div class="paso-badge">PASO 1</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Tus datos")

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

    col_edad, col_asignacion = st.columns(2)

    with col_edad:

        edad_retiro = st.number_input(
            "Edad de retiro a simular",
            min_value=60,
            max_value=65,
            value=st.session_state.get("edad_retiro", 60),
            step=1,
            key="edad_retiro_input",
            help="El cálculo de pensión Ley 73 aplica para edades entre 60 y 65 años.",
        )

    with col_asignacion:

        opciones_asignacion = {
            "Ninguna": "ninguna",
            "Cónyuge (esposa/esposo)": "conyuge",
            "Hijos": "hijos",
            "Padres": "padres",
            "Ayuda asistencial": "asistencia",
        }

        etiqueta_asignacion = st.selectbox(
            "Asignación familiar",
            options=list(opciones_asignacion.keys()),
            key="asignacion_input",
        )

    st.session_state.edad_retiro = int(edad_retiro)
    st.session_state.tipo_asignacion = opciones_asignacion[etiqueta_asignacion]

    st.session_state.datos_cliente = {
        "nombre": nombre.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip(),
    }


# ============================================================
# CARGA DEL PDF
# ============================================================

def cargar_pdf():

    st.markdown(
        '<div class="paso-badge">PASO 2</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Sube tu Constancia de Semanas Cotizadas")

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
        st.error("El módulo extractor.py todavía no está disponible correctamente.")
        return
        
    with st.spinner("Analizando tu información del IMSS y registrando prospecto..."):
        try:
            # 1. Ejecutar extracción del PDF
            resultado = analizar_pdf_streamlit(st.session_state.pdf)
            st.session_state.resultado_extraccion = resultado
            
            # 2. Sanitizar datos para la base de datos (Supabase espera tipos estrictos)
            semanas_raw = resultado.get("semanas_cotizadas", 0)
            semanas_int = int(float(semanas_raw)) if semanas_raw else 0
            
            sbc_raw = resultado.get("sbc_promedio", 0.0)
            sbc_float = float(sbc_raw) if sbc_raw else 0.0
            
            # Extraer NSS del diccionario o lista si viene múltiple
            nss_data = resultado.get("nss", None)
            nss_str = nss_data[0] if isinstance(nss_data, list) else str(nss_data)
            
            # Importar la función desde base_datos.py de forma local si es necesario
            from base_datos import guardar_prospecto
            
            # 3. Guardar el prospecto en Supabase de forma automática
            prospecto_guardado = guardar_prospecto(
                nombre=st.session_state.datos_cliente.get("nombre", "Usuario Web"),
                correo=st.session_state.datos_cliente.get("correo", ""),
                telefono=st.session_state.datos_cliente.get("telefono", ""),
                nss=nss_str,
                semanas_cotizadas=semanas_int,
                sbc_promedio=sbc_float,
                fecha_nacimiento=None, # Se actualizará en la etapa de simulación
                estatus_pago=st.session_state.pago_confirmado,
                codigo_promocional=st.session_state.codigo_promo if st.session_state.promo_validada else None
            )
            
            # 4. Almacenar el ID generado por Supabase para futuras actualizaciones o descargas
            if prospecto_guardado and "id" in prospecto_guardado:
                st.session_state.prospecto_id = prospecto_guardado["id"]

            # 5. Ejecutar el cálculo financiero real (pensión + Modalidad 40)
            if CALCULADOR_DISPONIBLE:

                try:
                    uma_actual = obtener_uma()
                except Exception:
                    uma_actual = 113.14

                try:

                    st.session_state.resultado_calculo = calcular_escenario(
                        sbc_promedio=sbc_float,
                        semanas=semanas_int,
                        edad=st.session_state.edad_retiro,
                        uma=uma_actual,
                        tipo_asignacion=st.session_state.tipo_asignacion,
                        meses_modalidad_40=st.session_state.meses_m40,
                    )

                except CalculadorPensionError as error:
                    st.session_state.resultado_calculo = None
                    st.warning(
                        f"No fue posible calcular tu escenario financiero: {error}"
                    )

            else:
                st.session_state.resultado_calculo = None

        except Ley97Error as error:
            st.session_state.resultado_extraccion = None
            st.error("❌ Este documento corresponde al régimen de Ley 97 del IMSS.")
            st.warning(str(error))
            return
        except SemanasInsuficientesError as error:
            st.session_state.resultado_extraccion = None
            st.warning(str(error))
            return
        except ExtractorPensionError as error:
            st.session_state.resultado_extraccion = None
            st.error(f"No fue posible analizar el documento: {error}")
            return
        except Exception as error:
            st.session_state.resultado_extraccion = None
            st.error("Ocurrió un error al procesar el PDF o guardar en la base de datos.")
            st.exception(error)
            return
            
    st.success("✅ Tu documento fue analizado y registrado correctamente.")

# ============================================================
# RESULTADO
# ============================================================

def mostrar_resultado():

    if not st.session_state.resultado_extraccion:
        return

    st.divider()

    st.markdown(
        '<div class="paso-badge">PASO 3</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Resultado de tu análisis")

    resultado = st.session_state.resultado_extraccion
    calculo = st.session_state.resultado_calculo

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

    col1, col2, col3 = st.columns(3)

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

    with col3:

        if calculo:

            pension_mensual = calculo.get(
                "pension", {}
            ).get("pension_final_mensual")

            st.metric(
                "Pensión mensual estimada",
                f"${pension_mensual:,.2f}" if pension_mensual is not None else "No disponible",
            )

        else:

            st.metric(
                "Pensión mensual estimada",
                "No disponible",
            )

    if calculo:

        st.caption(
            f"Estimación calculada para retiro a los "
            f"{st.session_state.edad_retiro} años. "
            "El reporte completo incluye la estrategia de "
            "Modalidad 40, inversión y retorno estimado."
        )

    else:

        st.caption(
            "El resultado es una estimación preliminar. "
            "El cálculo financiero completo se generará "
            "con el motor de simulación."
        )


# ============================================================
# PROMOCIÓN
# ============================================================

def validar_promocion():

    st.markdown(
        '<div class="paso-badge">PASO 4</div>',
        unsafe_allow_html=True,
    )
    st.subheader("¿Tienes un código promocional?")

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

    st.markdown(
        '<div class="paso-badge">PASO 5</div>',
        unsafe_allow_html=True,
    )
    st.subheader(
        "Reporte financiero completo"
    )

    st.write(
        "Obtén tu proyección financiera completa "
        "de Modalidad 40."
    )

    # ========================================================
    # PROMOCIÓN VÁLIDA
    # ========================================================

    if st.session_state.promo_validada:

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
        <div class="card-azul">

        <div class="precio">
        ${precio:,.0f} MXN
        </div>

        <div class="precio-detalle">
        Reporte financiero completo · pago único
        </div>

        <ul class="beneficios">
            <li>Proyección de pensión</li>
            <li>Análisis de Modalidad 40</li>
            <li>Inversión requerida</li>
            <li>Proyección mes a mes</li>
            <li>Costo acumulado</li>
            <li>Retorno de inversión (ROI)</li>
            <li>Escenarios de retiro</li>
        </ul>

        </div>
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

    st.markdown(
        """
        <div class="banner-desbloqueado">
            <div class="icono">🔓</div>
            <div class="texto-principal">
                Tu reporte financiero está desbloqueado
            </div>
            <div>Descárgalo en PDF a continuación.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # REGISTRAR USO DEL PROMO
    # ========================================================

    if st.session_state.promo_validada:

        registrar_uso_promo()

    # ========================================================
    # VALIDACIONES PREVIAS
    # ========================================================

    if not PDF_DISPONIBLE:

        st.error(
            "El módulo reporte_pdf.py todavía no está "
            "disponible correctamente."
        )

        return

    if not st.session_state.resultado_calculo:

        st.warning(
            "Aún no contamos con el cálculo financiero completo "
            "para generar tu PDF. Vuelve a procesar tu "
            "Constancia de Semanas Cotizadas."
        )

        return

    # ========================================================
    # GENERAR PDF (una sola vez, se guarda en session_state)
    # ========================================================

    if st.session_state.pdf_reporte_bytes is None:

        with st.spinner("Generando tu reporte PDF..."):

            try:

                nombre_cliente = st.session_state.datos_cliente.get(
                    "nombre", "Cliente Pensión 40"
                )

                st.session_state.pdf_reporte_bytes = generar_reporte_pdf(
                    nombre_cliente=nombre_cliente,
                    resultado_calculo=st.session_state.resultado_calculo,
                )

                st.session_state.reporte_generado = True

            except Exception as error:

                st.error(
                    "No fue posible generar el PDF de tu reporte."
                )

                st.exception(error)

                return

    # ========================================================
    # BOTÓN DE DESCARGA REAL
    # ========================================================

    nombre_archivo = "reporte_pension40.pdf"

    nombre_cliente_actual = st.session_state.datos_cliente.get("nombre", "")

    if nombre_cliente_actual:

        nombre_archivo = (
            "reporte_pension40_"
            f"{nombre_cliente_actual.strip().replace(' ', '_').lower()}.pdf"
        )

    st.download_button(
        label="📥 Descargar reporte PDF",
        data=st.session_state.pdf_reporte_bytes,
        file_name=nombre_archivo,
        mime="application/pdf",
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
