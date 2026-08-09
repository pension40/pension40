# ============================================================
# PENSION 40
# app.py
# Aplicación principal Streamlit
# ============================================================

import streamlit as st
from datetime import datetime

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
        proyectar_semanas_y_sbc_a_retiro,
        precalificar,
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
    "tiene_hijos": False,
    "proyeccion": None,
    "precalificacion": None,
    "modo_captura": "pdf",
    "datos_manuales_validos": False,
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
        --azul-claro: #EAF2FA;
        --azul-hover: #0F5A8F;
        --verde-ok: #14804A;
        --verde-claro: #E7F6ED;
        --rojo-alerta: #B3261E;
        --rojo-claro: #FCEAEA;
        --gris-texto: #3B3B3B;
        --gris-suave: #6B7280;
        --gris-borde: #E2E8F0;
        --gris-fondo: #F7F9FC;
    }

    /* Contenedor general más angosto y compacto */
    .main .block-container {
        max-width: 720px;
        padding-top: 1rem;
        padding-bottom: 2.5rem;
    }

    /* Reduce espacios verticales por default de Streamlit */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.4rem;
    }

    h1, h2, h3 { margin-bottom: 0.3rem; }

    /* ---------- ENCABEZADO COMPACTO ---------- */

    .header-wrap {
        text-align: center;
        margin-bottom: 0.8rem;
        padding-top: 0.2rem;
    }

    .titulo {
        text-align: center;
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }

    .subtitulo {
        text-align: center;
        font-size: 0.9rem;
        color: var(--gris-suave);
        font-weight: 500;
        margin-bottom: 0;
    }

    .linea-divisora {
        height: 3px;
        width: 60px;
        background: linear-gradient(90deg, var(--azul-medio), var(--azul-oscuro));
        margin: 0.5rem auto 0.9rem auto;
        border-radius: 4px;
    }

    /* ---------- TARJETAS COMPACTAS ---------- */

    .card {
        padding: 0.9rem 1.1rem;
        border-radius: 10px;
        border: 1px solid var(--gris-borde);
        background: #FFFFFF;
        box-shadow: 0 1px 4px rgba(11, 37, 69, 0.05);
        margin-bottom: 0.7rem;
    }

    .card h3, .card h4 {
        color: var(--azul-oscuro);
        margin-top: 0;
        font-size: 1rem;
    }

    .card-azul {
        padding: 0.9rem 1.1rem;
        border-radius: 10px;
        background: var(--azul-claro);
        border: 1px solid rgba(27, 108, 168, 0.2);
        margin-bottom: 0.7rem;
    }

    .card-compacta {
        padding: 0.6rem 0.9rem;
        border-radius: 8px;
        border: 1px solid var(--gris-borde);
        background: var(--gris-fondo);
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }

    /* ---------- PASO / SECCIÓN ---------- */

    .paso-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: var(--azul-oscuro);
        color: white;
        font-weight: 700;
        font-size: 0.72rem;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        margin-bottom: 0.4rem;
        letter-spacing: 0.02em;
    }

    /* ---------- MINI DASHBOARD DE MÉTRICAS ---------- */

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin: 0.5rem 0 0.6rem 0;
    }

    .metric-box {
        background: #FFFFFF;
        border: 1px solid var(--gris-borde);
        border-radius: 10px;
        padding: 0.6rem 0.4rem;
        text-align: center;
    }

    .metric-box .valor {
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        line-height: 1.15;
    }

    .metric-box .etiqueta {
        font-size: 0.68rem;
        color: var(--gris-suave);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        margin-top: 0.15rem;
    }

    /* ---------- PRECIO ---------- */

    .precio {
        text-align: center;
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin-bottom: 0.1rem;
    }

    .precio-detalle {
        text-align: center;
        font-size: 0.82rem;
        color: var(--gris-suave);
        margin-bottom: 0.4rem;
    }

    .centrado { text-align: center; }

    /* ---------- LISTA DE BENEFICIOS COMPACTA ---------- */

    .beneficios {
        list-style: none;
        padding-left: 0;
        margin: 0.4rem 0 0.1rem 0;
        columns: 2;
        column-gap: 1rem;
    }

    .beneficios li {
        padding: 0.15rem 0;
        color: var(--gris-texto);
        font-size: 0.82rem;
        break-inside: avoid;
    }

    .beneficios li::before {
        content: "✓";
        color: var(--verde-ok);
        font-weight: 800;
        margin-right: 0.4rem;
    }

    /* ---------- BOTONES ---------- */

    .stButton > button {
        width: 100%;
        min-height: 2.6rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.9rem;
        border: none;
        transition: transform 0.05s ease-in-out;
    }

    .stButton > button:hover { transform: translateY(-1px); }

    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--azul-medio), var(--azul-oscuro));
    }

    div[data-testid="stDownloadButton"] > button {
        width: 100%;
        min-height: 2.8rem;
        border-radius: 8px;
        font-weight: 700;
        background: linear-gradient(90deg, var(--verde-ok), #0F6B3C);
        color: white;
        border: none;
    }

    /* ---------- BANNER DE PRECALIFICACIÓN (TEASER) ---------- */

    .banner-precal {
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.6rem 0 0.8rem 0;
        text-align: center;
    }

    .banner-precal.ok {
        background: linear-gradient(135deg, var(--verde-claro), #F3FBF6);
        border: 1.5px solid rgba(20, 128, 74, 0.35);
    }

    .banner-precal.no {
        background: linear-gradient(135deg, var(--rojo-claro), #FDF4F4);
        border: 1.5px solid rgba(179, 38, 30, 0.3);
    }

    .banner-precal .icono { font-size: 1.6rem; }

    .banner-precal .titulo-banner {
        font-weight: 800;
        font-size: 1.05rem;
        margin: 0.25rem 0 0.1rem 0;
    }

    .banner-precal.ok .titulo-banner { color: var(--verde-ok); }
    .banner-precal.no .titulo-banner { color: var(--rojo-alerta); }

    .banner-precal .subtexto {
        font-size: 0.82rem;
        color: var(--gris-texto);
    }

    .banner-precal .pension-grande {
        font-size: 2rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin: 0.3rem 0;
    }

    /* ---------- BANNER DE DESBLOQUEO ---------- */

    .banner-desbloqueado {
        background: linear-gradient(90deg, #E6F4EA, #EFFAF2);
        border: 1px solid rgba(30, 138, 76, 0.35);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        text-align: center;
        margin-bottom: 0.7rem;
    }

    .banner-desbloqueado .icono { font-size: 1.5rem; }

    .banner-desbloqueado .texto-principal {
        font-weight: 800;
        color: var(--verde-ok);
        font-size: 1rem;
        margin: 0.2rem 0 0.05rem 0;
    }

    /* ---------- TABS MÁS COMPACTAS ---------- */

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 2.4rem;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* ---------- FOOTER ---------- */

    .footer {
        text-align: center;
        font-size: 0.72rem;
        color: var(--gris-suave);
        margin-top: 1.8rem;
        line-height: 1.4;
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

    col_correo, col_tel = st.columns(2)

    with col_correo:

        correo = st.text_input(
            "Correo electrónico",
            placeholder="correo@ejemplo.com",
            key="correo_cliente",
        )

    with col_tel:

        telefono = st.text_input(
            "WhatsApp",
            placeholder="10 dígitos",
            key="telefono_cliente",
        )

    col_edad, col_hijos, col_asignacion = st.columns(3)

    with col_edad:

        edad_retiro = st.number_input(
            "Edad de retiro",
            min_value=60,
            max_value=65,
            value=st.session_state.get("edad_retiro", 60),
            step=1,
            key="edad_retiro_input",
            help="Edad a la que planeas pensionarte (60 a 65 años).",
        )

    with col_hijos:

        tiene_hijos = st.selectbox(
            "¿Tienes hijos?",
            options=["No", "Sí"],
            key="hijos_input",
            help="Los hijos menores o en edad de estudiar pueden dar derecho a asignación familiar.",
        )

    with col_asignacion:

        opciones_asignacion = {
            "Ninguna": "ninguna",
            "Cónyuge": "conyuge",
            "Hijos": "hijos",
            "Padres": "padres",
            "Asistencial": "asistencia",
        }

        etiqueta_default = (
            "Hijos" if tiene_hijos == "Sí" else "Ninguna"
        )

        etiqueta_asignacion = st.selectbox(
            "Asignación familiar",
            options=list(opciones_asignacion.keys()),
            index=list(opciones_asignacion.keys()).index(
                etiqueta_default
            ),
            key="asignacion_input",
        )

    st.session_state.edad_retiro = int(edad_retiro)
    st.session_state.tiene_hijos = (tiene_hijos == "Sí")
    st.session_state.tipo_asignacion = opciones_asignacion[etiqueta_asignacion]

    st.session_state.datos_cliente = {
        "nombre": nombre.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip(),
    }


# ============================================================
# ENTRADA DE DATOS IMSS: PDF O CAPTURA MANUAL
# ============================================================

def cargar_pdf():

    st.markdown(
        '<div class="paso-badge">PASO 2</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Datos del IMSS")

    tab_pdf, tab_manual = st.tabs(
        ["📄 Subir Constancia (PDF)", "✏️ Captura manual"]
    )

    with tab_pdf:

        st.caption(
            "Sube el PDF de tu Constancia de Semanas Cotizadas del IMSS."
        )

        archivo = st.file_uploader(
            "Seleccionar PDF",
            type=["pdf"],
            accept_multiple_files=False,
            key="archivo_imss",
            label_visibility="collapsed",
        )

        if archivo:

            st.session_state.pdf = archivo
            st.session_state.modo_captura = "pdf"

            st.success(
                f"📎 {archivo.name} ({archivo.size / 1024:.0f} KB)"
            )

    with tab_manual:

        st.caption(
            "¿No tienes el PDF a la mano? Captura tus datos manualmente."
        )

        col_m1, col_m2 = st.columns(2)

        with col_m1:

            semanas_manual = st.number_input(
                "Semanas cotizadas actuales",
                min_value=0,
                max_value=3000,
                value=0,
                step=1,
                key="semanas_manual",
            )

        with col_m2:

            sbc_manual = st.number_input(
                "SBC promedio diario ($)",
                min_value=0.0,
                max_value=10000.0,
                value=0.0,
                step=10.0,
                key="sbc_manual",
            )

        fecha_nac_manual = st.date_input(
            "Fecha de nacimiento",
            value=None,
            min_value=datetime(1940, 1, 1),
            max_value=datetime.now(),
            key="fecha_nac_manual",
            format="DD/MM/YYYY",
        )

        primera_fecha_manual = st.date_input(
            "Fecha de tu primera cotización IMSS",
            value=None,
            min_value=datetime(1940, 1, 1),
            max_value=datetime.now(),
            key="primera_fecha_manual",
            format="DD/MM/YYYY",
            help="Necesaria para confirmar si aplicas para Ley 73 (antes del 1 de julio de 1997).",
        )

        if st.button(
            "Usar estos datos manuales",
            key="btn_usar_manual",
        ):

            if semanas_manual <= 0 or sbc_manual <= 0 or not fecha_nac_manual or not primera_fecha_manual:

                st.error(
                    "Completa semanas, SBC, fecha de nacimiento "
                    "y primera fecha de cotización."
                )
                st.session_state.datos_manuales_validos = False

            else:

                st.session_state.modo_captura = "manual"
                st.session_state.datos_manuales_validos = True

                fecha_nacimiento_dt = datetime(
                    fecha_nac_manual.year,
                    fecha_nac_manual.month,
                    fecha_nac_manual.day,
                )

                primera_fecha_dt = datetime(
                    primera_fecha_manual.year,
                    primera_fecha_manual.month,
                    primera_fecha_manual.day,
                )

                edad_actual_manual = (
                    datetime.now().year - fecha_nacimiento_dt.year
                    - (
                        (datetime.now().month, datetime.now().day)
                        < (fecha_nacimiento_dt.month, fecha_nacimiento_dt.day)
                    )
                )

                ley_73_manual = primera_fecha_dt <= datetime(1997, 6, 30)

                st.session_state.resultado_extraccion = {
                    "nombre": st.session_state.datos_cliente.get("nombre", ""),
                    "nss": None,
                    "curp": None,
                    "fecha_nacimiento": fecha_nacimiento_dt,
                    "edad_actual": edad_actual_manual,
                    "primera_fecha_cotizacion": primera_fecha_dt,
                    "ley_73": ley_73_manual,
                    "semanas_cotizadas": float(semanas_manual),
                    "sbc_promedio": float(sbc_manual),
                }

                st.success(
                    "Datos manuales cargados. Ya puedes calcular tu precalificación."
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

    modo = st.session_state.modo_captura

    if modo == "pdf" and st.session_state.pdf is None:
        errores.append(
            "Sube tu Constancia de Semanas Cotizadas o usa la captura manual."
        )

    if modo == "manual" and not st.session_state.datos_manuales_validos:
        errores.append(
            "Completa y confirma tus datos manuales (botón 'Usar estos datos manuales')."
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

    modo = st.session_state.modo_captura

    # --------------------------------------------------------
    # MODO PDF: ejecutar extracción real
    # --------------------------------------------------------

    if modo == "pdf":

        if not EXTRACTOR_DISPONIBLE:
            st.error("El módulo extractor.py todavía no está disponible correctamente.")
            return

        with st.spinner("Analizando tu información del IMSS..."):
            try:
                resultado = analizar_pdf_streamlit(st.session_state.pdf)
                st.session_state.resultado_extraccion = resultado

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
                st.error("Ocurrió un error al procesar el PDF.")
                st.exception(error)
                return

    # --------------------------------------------------------
    # A partir de aquí, "resultado_extraccion" ya existe
    # (llenado por el PDF arriba, o por la captura manual en
    # cargar_pdf()).
    # --------------------------------------------------------

    resultado = st.session_state.resultado_extraccion

    if not resultado:
        st.error("No hay datos del IMSS para calcular. Sube tu PDF o usa la captura manual.")
        return

    # --------------------------------------------------------
    # Proyección de semanas y SBC a la edad de retiro elegida
    # --------------------------------------------------------

    if not CALCULADOR_DISPONIBLE:
        st.error("El módulo calculador.py todavía no está disponible correctamente.")
        return

    try:
        uma_actual = obtener_uma()
    except Exception:
        uma_actual = 113.14

    fecha_nacimiento = resultado.get("fecha_nacimiento")

    try:

        if fecha_nacimiento:

            proyeccion = proyectar_semanas_y_sbc_a_retiro(
                fecha_nacimiento=fecha_nacimiento,
                semanas_actuales=float(resultado.get("semanas_cotizadas") or 0),
                sbc_promedio_actual=float(resultado.get("sbc_promedio") or 0),
                edad_retiro_deseada=st.session_state.edad_retiro,
            )

        else:

            # Sin fecha de nacimiento no se puede proyectar a
            # futuro; se usa el estado actual como aproximación.
            proyeccion = {
                "edad_actual": resultado.get("edad_actual"),
                "fecha_retiro_estimada": None,
                "anios_para_retiro": None,
                "semanas_actuales": float(resultado.get("semanas_cotizadas") or 0),
                "semanas_adicionales_estimadas": 0,
                "semanas_totales_estimadas": float(resultado.get("semanas_cotizadas") or 0),
                "sbc_promedio_proyectado": float(resultado.get("sbc_promedio") or 0),
            }

        st.session_state.proyeccion = proyeccion

        precal = precalificar(
            ley_73=bool(resultado.get("ley_73")),
            semanas_totales_estimadas=proyeccion["semanas_totales_estimadas"],
            sbc_promedio=proyeccion["sbc_promedio_proyectado"],
            edad_retiro_deseada=st.session_state.edad_retiro,
            uma=uma_actual,
            tipo_asignacion=st.session_state.tipo_asignacion,
        )

        st.session_state.precalificacion = precal

        if precal.get("califica"):

            st.session_state.resultado_calculo = calcular_escenario(
                sbc_promedio=proyeccion["sbc_promedio_proyectado"],
                semanas=proyeccion["semanas_totales_estimadas"],
                edad=st.session_state.edad_retiro,
                uma=uma_actual,
                tipo_asignacion=st.session_state.tipo_asignacion,
                meses_modalidad_40=st.session_state.meses_m40,
            )

        else:

            st.session_state.resultado_calculo = None

    except (CalculadorPensionError, ValueError) as error:

        st.session_state.proyeccion = None
        st.session_state.precalificacion = None
        st.session_state.resultado_calculo = None
        st.warning(f"No fue posible calcular tu precalificación: {error}")
        return

    # --------------------------------------------------------
    # Registrar prospecto en Supabase (best-effort, no bloquea
    # el flujo si falla).
    # --------------------------------------------------------

    try:

        semanas_int = int(float(resultado.get("semanas_cotizadas") or 0))
        sbc_float = float(resultado.get("sbc_promedio") or 0)

        nss_data = resultado.get("nss")
        nss_str = nss_data[0] if isinstance(nss_data, list) else (str(nss_data) if nss_data else "")

        from base_datos import guardar_prospecto

        prospecto_guardado = guardar_prospecto(
            nombre=st.session_state.datos_cliente.get("nombre", "Usuario Web"),
            correo=st.session_state.datos_cliente.get("correo", ""),
            telefono=st.session_state.datos_cliente.get("telefono", ""),
            nss=nss_str,
            semanas_cotizadas=semanas_int,
            sbc_promedio=sbc_float,
            fecha_nacimiento=None,
            estatus_pago=st.session_state.pago_confirmado,
            codigo_promocional=st.session_state.codigo_promo if st.session_state.promo_validada else None,
        )

        if prospecto_guardado and "id" in prospecto_guardado:
            st.session_state.prospecto_id = prospecto_guardado["id"]

    except Exception:
        # Registrar el prospecto es best-effort: si Supabase
        # falla, el usuario debe poder seguir viendo su
        # precalificación de todas formas.
        pass

    st.success("✅ Precalificación lista.")


# ============================================================
# RESULTADO: BANNER DE PRECALIFICACIÓN
# ============================================================

def mostrar_resultado():

    if not st.session_state.resultado_extraccion:
        return

    if not st.session_state.precalificacion:
        return

    st.markdown(
        '<div class="paso-badge">PASO 3</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Tu precalificación")

    resultado = st.session_state.resultado_extraccion
    proyeccion = st.session_state.proyeccion
    precal = st.session_state.precalificacion

    edad_retiro = st.session_state.edad_retiro

    # --------------------------------------------------------
    # Mini dashboard de métricas (siempre visible)
    # --------------------------------------------------------

    semanas_hoy = resultado.get("semanas_cotizadas")
    semanas_proyectadas = proyeccion.get("semanas_totales_estimadas") if proyeccion else semanas_hoy
    sbc = proyeccion.get("sbc_promedio_proyectado") if proyeccion else resultado.get("sbc_promedio")

    ley_73_texto = "Ley 73 ✓" if resultado.get("ley_73") else "Ley 97"

    fecha_retiro_txt = "—"
    if proyeccion and proyeccion.get("fecha_retiro_estimada"):
        fecha_retiro_txt = proyeccion["fecha_retiro_estimada"].strftime("%m/%Y")

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-box">
                <div class="valor">{ley_73_texto}</div>
                <div class="etiqueta">Régimen</div>
            </div>
            <div class="metric-box">
                <div class="valor">{semanas_proyectadas:,.0f}</div>
                <div class="etiqueta">Semanas a los {edad_retiro} años</div>
            </div>
            <div class="metric-box">
                <div class="valor">${sbc:,.0f}</div>
                <div class="etiqueta">SBC promedio</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Banner llamativo de precalificación
    # --------------------------------------------------------

    if precal.get("califica"):

        pension_mensual = precal.get("pension_mensual_estimada", 0)

        st.markdown(
            f"""
            <div class="banner-precal ok">
                <div class="icono">🎉</div>
                <div class="titulo-banner">¡Buenas noticias! Precalificas para Ley 73</div>
                <div class="pension-grande">${pension_mensual:,.0f}<span style="font-size:1rem;">/mes</span></div>
                <div class="subtexto">
                    Pensión mensual estimada al retirarte a los {edad_retiro} años.
                    Esto es solo el punto de partida — con la estrategia de
                    Modalidad&nbsp;40 tu pensión puede ser considerablemente mayor.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="centrado" style="font-weight:700; color:var(--azul-oscuro); margin-bottom:0.3rem;">
                ¿Quieres que te haga el precálculo completo de Modalidad 40?
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        razon = precal.get("razon", "No fue posible precalificar con los datos disponibles.")

        st.markdown(
            f"""
            <div class="banner-precal no">
                <div class="icono">⚠️</div>
                <div class="titulo-banner">Este escenario no precalifica</div>
                <div class="subtexto">{razon}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "semanas_faltantes" in precal:

            st.caption(
                "💡 Tip: retrasar tu edad de retiro o continuar cotizando "
                "más tiempo puede ayudarte a cubrir las semanas faltantes."
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

    precal = st.session_state.precalificacion

    if not precal or not precal.get("califica"):
        # No tiene sentido ofrecer el reporte completo de
        # Modalidad 40 a alguien que no precalificó (Ley 97 o
        # semanas insuficientes): el banner rojo en
        # mostrar_resultado() ya le explica por qué.
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
        "🔍 Ver mi precalificación",
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
