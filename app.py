# ============================================================
# PENSION 40
# app.py - Aplicación principal Streamlit (Bloque 1 de 4)
# ============================================================

import streamlit as st
import pandas as pd
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

from calculador import calcular_escenario, resumen_escenario

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
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Pensión 40",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

NOMBRE_APP = "Pensión 40"
PRECIO_REPORTE_DEFAULT = 249

# ============================================================
# SESSION STATE (ESTADO DE LA SESIÓN)
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
# ESTILOS CSS INYECTADOS
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
# PENSION 40
# app.py - Aplicación principal Streamlit (Bloque 2 de 4)
# ============================================================

def mostrar_encabezado():
    st.markdown('<div class="titulo">Pensión 40</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Simulador financiero de pensión bajo Ley 73 del IMSS</div>', unsafe_allow_html=True)

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

def capturar_datos():
    st.subheader("1. Tus datos")
    nombre = st.text_input("Nombre completo", placeholder="Nombre y apellidos", key="nombre_cliente")
    correo = st.text_input("Correo electrónico", placeholder="correo@ejemplo.com", key="correo_cliente")
    telefono = st.text_input("WhatsApp", placeholder="10 dígitos", key="telefono_cliente")
    
    st.session_state.datos_cliente = {
        "nombre": nombre.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip(),
    }

def cargar_pdf():
    st.subheader("2. Sube tu Constancia de Semanas Cotizadas")
    st.write("El documento debe ser el PDF emitido por el IMSS.")
    archivo = st.file_uploader("Seleccionar PDF", type=["pdf"], accept_multiple_files=False, key="archivo_imss")
    if archivo:
        st.session_state.pdf = archivo
        st.success(f"PDF recibido: {archivo.name}")
        st.caption(f"Tamaño: {archivo.size / 1024:.1f} KB")

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
        errores.append("Debes subir tu Constancia de Semanas Cotizadas.")
    return errores

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
            # 1. Extracción del contenido del PDF
            resultado = analizar_pdf_streamlit(st.session_state.pdf)
            st.session_state.resultado_extraccion = resultado
            
            # 2. Sanitización estricta de tipos numéricos para Supabase
            semanas_raw = resultado.get("semanas_cotizadas", 0)
            semanas_int = int(float(semanas_raw)) if semanas_raw else 0
            
            sbc_raw = resultado.get("sbc_promedio", 0.0)
            sbc_float = float(sbc_raw) if sbc_raw else 0.0
            
            nss_data = resultado.get("nss", None)
            nss_str = nss_data[0] if isinstance(nss_data, list) else str(nss_data)
            
            # 3. Guardado directo y seguro en Supabase
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
                codigo_promocional=st.session_state.codigo_promo if st.session_state.promo_validada else None
            )
            
            if prospecto_guardado and "id" in prospecto_guardado:
                st.session_state.prospecto_id = prospecto_guardado["id"]
                
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
            st.error("Ocurrió un error inesperado al procesar el documento.")
            st.exception(error)
            return
            
    st.success("✅ Tu documento fue analizado y registrado correctamente.")
# ============================================================
# PENSION 40
# app.py - Aplicación principal Streamlit (Bloque 3 de 4)
# ============================================================

def mostrar_resultado():
    if not st.session_state.resultado_extraccion:
        return
    st.divider()
    st.subheader("3. Resultado de tu análisis preliminar")
    resultado = st.session_state.resultado_extraccion
    semanas = resultado.get("semanas_cotizadas", "No disponible")
    sbc = resultado.get("sbc_promedio", None)
    
    st.markdown('<div class="card"><h3>🎯 Resumen Obtenido de tu PDF</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Semanas cotizadas", semanas)
    with col2:
        if sbc is not None:
            st.metric("SBC promedio (Últimas 250 semanas)", f"${float(sbc):,.2f}")
        else:
            st.metric("SBC promedio", "No disponible")
    st.caption("El cálculo financiero completo e interactivo se habilitará en la sección inferior.")

def mostrar_descarga_reporte():
    st.write("---")
    st.markdown("<h3 style='color: #2E7D32;'>📊 Proyección Financiera Interactiva (Desbloqueada)</h3>", unsafe_allow_html=True)
    st.write("Modifica los valores para recalcular los escenarios de tu estrategia en tiempo real:")
    
    resultado_ext = st.session_state.resultado_extraccion
    
    try:
        uma_sistema = obtener_uma()
    except Exception:
        uma_sistema = 117.31

    # CONTROLES DINÁMICOS
    col_in1, col_input2, col_input3 = st.columns(3)
    with col_in1:
        edad_retiro = st.slider("Edad planeada de Retiro", min_value=60, max_value=65, value=65, step=1)
    with col_input2:
        meses_m40 = st.number_input("Meses a cotizar en M40", min_value=1, max_value=120, value=60, step=6)
    with col_input3:
        salario_propuesto = st.number_input("Salario Diario de Inscripción M40 ($)", min_value=100.0, max_value=4000.0, value=float(uma_sistema * 25), step=100.0)

    # RE-CÁLCULO MATEMÁTICO EN TIEMPO REAL
    try:
        escenario = calcular_escenario(
            sbc_promedio=float(resultado_ext.get("sbc_promedio", 0)),
            semanas=float(resultado_ext.get("semanas_cotizadas", 0)),
            edad=edad_retiro,
            uma=uma_sistema,
            tipo_asignacion="asistencia",
            salario_modalidad_40=salario_propuesto,
            meses_modalidad_40=meses_m40,
            aplicar_fox=True
        )
        resumen = resumen_escenario(escenario)
    except Exception as e:
        st.error("Error al procesar los parámetros en el motor de cálculo.")
        st.exception(e)
        return

    st.session_state.resultado_calculo = escenario

    # RENDERIZADO DEL DASHBOARD EJECUTIVO
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Pensión Estimada Mensual", value=f"${resumen.get('Pensión estimada mensual', 0):,.2f} MXN", delta="Con Factor Fox")
    with m2:
        st.metric(label="Inversión M40 Total", value=f"${resumen.get('Inversión Modalidad 40', 0):,.2f} MXN")
    with m3:
        st.metric(label="Retorno Estimado (ROI)", value=f"{resumen.get('ROI estimado meses', 0)} Meses", delta=f"~ {escenario['roi']['anios']} Años", delta_color="inverse")

    # DESPLIEGUE DEL GRÁFICO INTERACTIVO DE PAGO ACUMULADO
    st.markdown("#### 📈 Historial de Crecimiento de Inversión")
    tabla_mensual_data = escenario["modalidad_40"]["inversion"]["tabla_mensual"]
    if tabla_mensual_data:
        df_inversion = pd.DataFrame(tabla_mensual_data)
        df_inversion.rename(columns={"mes": "Mes de Aportación", "inversion_acumulada": "Inversión Acumulada ($)"}, inplace=True)
        st.line_chart(data=df_inversion, x="Mes de Aportación", y="Inversión Acumulada ($)", use_container_width=True)

    with st.expander("🔍 Ver Factores Técnicos de Resolución Jurídica"):
        st.write(f"**Grupo Salarial Base:** {resumen.get('Grupo salarial')}")
        st.write(f"**Porcentaje de Cuantía Básica:** {resumen.get('Cuantía básica')}")
        st.write(f"**Incrementos Anuales Reconocidos:** {resumen.get('Incrementos anuales')} bloques")
        st.write(f"**Salario diario real registrado ante M40:** ${resumen.get('Salario Modalidad 40'):,.2f}")

    # CONSTRUCCIÓN DE LA CONSTANCIA DIGITAL EJECUTIVA
    if st.session_state.promo_validada:
        registrar_uso_promo()

    reporte_documento = f"""========================================================================
                  PENSIÓN 40 - REPORTE EJECUTIVO DE SIMULACIÓN
========================================================================
FECHA DE EMISIÓN: {datetime.now().strftime('%d/%m/%Y')}
------------------------------------------------------------------------
Nombre Completo: {st.session_state.datos_cliente.get('nombre', 'Usuario')}
WhatsApp Registrado: {st.session_state.datos_cliente.get('telefono', 'No registrado')}
Semanas Totales del PDF: {resumen.get('Semanas cotizadas')} Semanas
------------------------------------------------------------------------
ESTRATEGIA FINANCIERA (MODALIDAD 40):
Salario Diario de Inscripción: ${resumen.get('Salario Modalidad 40'):,.2f} MXN diarios
Duración Planeada de las Aportaciones: {meses_m40} Meses
Inversión Financiera Total Requerida: ${resumen.get('Inversión Modalidad 40'):,.2f} MXN
------------------------------------------------------------------------
DICTAMEN DE PENSIÓN FINAL LEY 1973:
PENSIÓN MENSUAL ESTIMADA (A LOS {edad_retiro} AÑOS): ${resumen.get('Pensión estimada mensual', 0):,.2f} MXN
TIEMPO ESTIMADO DE RECUPERACIÓN (ROI): {resumen.get('ROI estimado meses', 0)} MESES
========================================================================"""

    st.write("---")
    st.download_button(
        label="📥 Descargar Reporte Ejecutivo Validado",
        data=reporte_documento,
        file_name=f"Constancia_Proyeccion_M40_{st.session_state.datos_cliente.get('nombre', 'Cliente').replace(' ', '_')}.txt",
        mime="text/plain",
        key="btn_descarga_pdf_profesional_desbloqueado"
    )

def mostrar_acceso_reporte():
    if not st.session_state.resultado_extraccion:
        return
        
    st.divider()
    st.subheader("5. Reporte financiero completo")
    
    if st.session_state.promo_validada:
        mostrar_descarga_reporte()
        return
        
    try:
        precio = obtener_precio_reporte()
    except Exception:
        precio = PRECIO_REPORTE_DEFAULT
        
    st.markdown(f'<div class="card"><div class="precio">${precio:,.0f} MXN</div><div class="centrado">Reporte financiero completo</div></div>', unsafe_allow_html=True)
    st.write("El reporte incluye proyecciones mes a mes, costo acumulado, retorno de inversión y escenarios de retiro.")
    
    if not st.session_state.pago_confirmado:
        if st.button(f"💳 Obtener reporte por ${precio:,.0f} MXN", type="primary", key="btn_pago"):
            st.info("La pasarela de pago se conectará en la siguiente etapa.")
    else:
        mostrar_descarga_reporte()
# ============================================================
# PENSION 40
# app.py - Aplicación principal Streamlit (Bloque 4 de 4)
# ============================================================

def validar_promocion():
    st.subheader("4. ¿Tienes un código promocional?")
    st.write("Si recibiste un código promocional de Pensión 40, puedes ingresarlo aquí.")
    codigo = st.text_input("Código promocional", placeholder="Ejemplo: P40-PRUEBA", key="codigo_promocional")
    
    if st.button("Validar código promocional", key="btn_validar_promo"):
        if not codigo.strip():
            st.warning("Ingresa un código promocional.")
            return
        codigo = codigo.strip().upper()
        with st.spinner("Validando código promocional..."):
            try:
                resultado = validar_codigo_promocional(codigo)
            except Exception as error:
                st.error("No fue posible comunicarse con la base de datos de Supabase.")
                st.exception(error)
                return
                
            if resultado.get("valido"):
                st.session_state.codigo_promo = codigo
                st.session_state.promo_validada = True
                st.success("🎉 ¡Código promocional válido!")
                st.rerun()
            else:
                st.session_state.codigo_promo = ""
                st.session_state.promo_validada = False
                st.error(resultado.get("mensaje", "El código promocional no es válido."))

def registrar_uso_promo():
    if not st.session_state.promo_validada:
        return True
    if st.session_state.promo_uso_registrado:
        return True
    codigo = st.session_state.codigo_promo
    if not codigo:
        return False
    try:
        registrar_uso_promocion(codigo)
        st.session_state.promo_uso_registrado = True
        return True
    except Exception as error:
        st.error("El código fue validado, pero no fue posible registrar su uso en Supabase.")
        st.exception(error)
        return False

def panel_administrador():
    st.divider()
    with st.expander("⚙️ Administración"):
        if not st.session_state.admin_autenticado:
            st.subheader("Acceso administrativo")
            password = st.text_input("Contraseña", type="password", key="password_admin")
            if st.button("🔐 Ingresar", key="btn_admin_login"):
                try:
                    correcto = verificar_password_admin(password)
                except Exception as error:
                    st.error("No fue posible verificar la contraseña en Supabase.")
                    st.exception(error)
                    return
                if correcto:
                    st.session_state.admin_autenticado = True
                    st.success("Administrador autenticado.")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")
                    return
            return

        st.success("Administrador autenticado.")
        st.subheader("⚙️ Configuración de Pensión 40")
        
        try:
            uma_actual = obtener_uma()
        except Exception:
            uma_actual = 117.31
        uma_nueva = st.number_input("Valor actual de UMA", min_value=0.01, value=float(uma_actual), step=0.01, format="%.2f", key="uma_admin")
        
        if st.button("Guardar UMA", key="btn_guardar_uma"):
            try:
                actualizar_uma(uma_nueva)
                st.success("✅ UMA actualizada correctamente en Supabase.")
            except Exception as error:
                st.error("No fue posible actualizar la UMA.")
                st.exception(error)
                
        st.divider()
        st.subheader("🎟️ Crear promoción")
        codigo = st.text_input("Nuevo código", placeholder="Ej. P40-FACEBOOK-AGOSTO", key="nuevo_codigo")
        col1, col2 = st.columns(2)
        with col1:
            activo = st.checkbox("Código ACTIVO", value=True, key="nuevo_codigo_activo")
        with col2:
            limite = st.number_input("Límite de usos", min_value=0, value=100, step=1, key="limite_codigo")
            
        if st.button("➕ Crear promoción", key="btn_crear_promo"):
            if not codigo.strip():
                st.warning("Ingresa un código.")
            else:
                try:
                    estatus = "ACTIVO" if activo else "INACTIVO"
                    crear_codigo_promocional(codigo=codigo, limite_usos=limite, estatus=estatus)
                    st.success(f"✅ Promoción {codigo.upper()} creada correctamente.")
                    st.rerun()
                except Exception as error:
                    st.error("No fue posible crear la promoción.")
                    st.exception(error)
                    
        st.divider()
        st.subheader("📋 Promociones existentes")
        try:
            promociones = obtener_promociones()
        except Exception as error:
            st.error("No fue posible obtener las promociones desde Supabase.")
            st.exception(error)
            promociones = []
            
        if not promociones:
            st.info("No existen promociones registradas.")
        else:
            for promo in promociones:
                codigo_existente = promo.get("codigo", "")
                estatus_actual = promo.get("estatus", "INACTIVO")
                usos = promo.get("usos_actuales", 0)
                limite_usos = promo.get("limite_usos", 0)
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{codigo_existente}**")
                    st.caption(f"Usos: {usos} / {limite_usos if limite_usos else '∞'}")
                with col2:
                    st.write(estatus_actual)
                with col3:
                    if estatus_actual == "ACTIVO":
                        if st.button("Desactivar", key=f"desactivar_{codigo_existente}"):
                            try:
                                cambiar_estatus_promocion(codigo_existente, "INACTIVO")
                                st.rerun()
                            except Exception:
                                st.error("No se desactivó.")
                    else:
                        if st.button("Activar", key=f"activar_{codigo_existente}"):
                            try:
                                cambiar_estatus_promocion(codigo_existente, "ACTIVO")
                                st.rerun()
                            except Exception:
                                st.error("No se activó.")

        st.divider()
        if st.button("Cerrar sesión administrativa", key="btn_admin_logout"):
            st.session_state.admin_autenticado = False
            st.rerun()

def mostrar_aviso_legal():
    st.markdown('<div class="footer">Pensión 40 · Simulador financiero Ley 73 IMSS<br><br>Las proyecciones generadas por este sistema son estimaciones financieras y no constituyen una resolución oficial del Instituto Mexicano del Seguro Social.</div>', unsafe_allow_html=True)

def main():
    mostrar_encabezado()
    mostrar_presentacion()
    capturar_datos()
    cargar_pdf()
    st.divider()
    if st.button("🚀 Calcular mi potencial de pensión", type="primary", key="btn_calcular"):
        procesar_informacion()
    mostrar_resultado()
    if st.session_state.resultado_extraccion:
        validar_promocion()
        mostrar_acceso_reporte()
    mostrar_aviso_legal()
    panel_administrador()

if __name__ == "__main__":
    main()

