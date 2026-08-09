# ============================================================
# PENSION 40
# app.py - CÓDIGO COMPLETO Y CORREGIDO (Bloque 1 de 3)
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA (DEBE SER LA PRIMERÍSIMA LÍNEA DE ST)
# ============================================================
st.set_page_config(
    page_title="Pensión 40",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# MÓDULOS DE CONEXIÓN CON LA BASE DE DATOS
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

# MOTOR MATEMÁTICO FINANCIERO
from calculador import calcular_escenario, resumen_escenario

# COMPONENTE GENERADOR DE REPORTE EJECUTIVO PDF
try:
    from reporte_pdf import generar_reporte_pdf
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

# EXTRACTOR AUTOMATIZADO DE EXPIEDIENTES IMSS
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

# INYECCIÓN CENTRALIZADA DE ESTILOS Y LOGO CORPORATIVO
from estilos import inyectar_estilos, mostrar_encabezado, mostrar_pie_de_pagina

# INYECTAR HOJA DE ESTILOS INMEDIATAMENTE
inyectar_estilos()

PRECIO_REPORTE_DEFAULT = 249

# ============================================================
# INICIALIZACIÓN ROBUSTA DEL ESTADO DE SESIÓN
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
    "pago_mensual_m40": 5000.0,
    "salario_modalidad_40": None,
}

for clave, valor in valores_iniciales.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor


# ============================================================
# FORMULARIOS VISUALES DE CAPTURA
# ============================================================
def mostrar_presentacion():
    st.markdown(
        """
        <div class="card">
            <h3 style='margin-top:0;'>📊 Proyección Estratégica de Retiro</h3>
            Analizamos tu Constancia de Semanas Cotizadas del IMSS para validar tu derecho al régimen de la <b>Ley 73</b> y optimizar financieramente tu pensión.
        </div>
        """,
        unsafe_allow_html=True,
    )

def capturar_datos():
    st.markdown('<div class="paso-badge">PASO 1</div>', unsafe_allow_html=True)
    st.subheader("Ingresa tus datos de contacto")
    
    nombre = st.text_input("Nombre completo", placeholder="Ej. Juan Pérez López", key="nombre_cliente")
    col_correo, col_tel = st.columns(2)
    with col_correo:
        correo = st.text_input("Correo electrónico", placeholder="correo@ejemplo.com", key="correo_cliente")
    with col_tel:
        telefono = st.text_input("WhatsApp (10 dígitos)", placeholder="3312345678", key="telefono_cliente")
        
    st.session_state.datos_cliente = {
        "nombre": nombre.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip(),
    }

def cargar_pdf():
    st.markdown('<div class="paso-badge">PASO 2</div>', unsafe_allow_html=True)
    st.subheader("Carga tu información oficial del IMSS")
    
    archivo = st.file_uploader("Selecciona el archivo PDF de tus semanas cotizadas", type=["pdf"], key="archivo_imss", label_visibility="collapsed")
    if archivo:
        st.session_state.pdf = archivo
        st.session_state.modo_captura = "pdf"
        st.success(f"✓ Documento listo para análisis: {archivo.name}")
# ============================================================
# PENSION 40
# app.py - CÓDIGO COMPLETO Y CORREGIDO (Bloque 2 de 3)
# ============================================================

def validar_datos():
    errores = []
    datos = st.session_state.datos_cliente
    if not datos.get("nombre"): errores.append("Por favor, escribe tu nombre completo.")
    if not datos.get("correo"): errores.append("Por favor, ingresa tu correo electrónico.")
    if not datos.get("telefono"): errores.append("Por favor, introduce tu número de WhatsApp.")
    if st.session_state.pdf is None: errores.append("Es necesario subir tu archivo PDF de Semanas Cotizadas.")
    return errores

def BlackBox_calcular_sbc_ponderado(sbc_actual, sbc_m40, meses_m40):
    """Calcula de forma exacta el peso ponderado del salario según los meses invertidos."""
    if meses_m40 >= 58:
        return sbc_m40
    dias_m40 = meses_m40 * 30.4
    dias_restantes = max(0.0, 1750.0 - dias_m40)
    return ((sbc_actual * dias_restantes) + (sbc_m40 * dias_m40)) / 1750.0

def procesar_informacion():
    errores = validar_datos()
    if errores:
        for err in errores: st.error(err)
        return
        
    if not EXTRACTOR_DISPONIBLE:
        st.error("El módulo extractor.py todavía no está disponible.")
        return
        
    with st.spinner("Procesando historial y auditando derechos Ley 73..."):
        try:
            resultado = analizar_pdf_streamlit(st.session_state.pdf)
            st.session_state.resultado_extraccion = resultado
            
            semanas_int = int(float(resultado.get("semanas_cotizadas", 0)))
            sbc_float = float(resultado.get("sbc_promedio", 0.0))
            nss_data = resultado.get("nss", "")
            nss_str = nss_data[0] if isinstance(nss_data, list) and nss_data else str(nss_data)
            
            from base_datos import guardar_prospecto
            prospecto_guardado = guardar_prospecto(
                nombre=st.session_state.datos_cliente.get("nombre"),
                correo=st.session_state.datos_cliente.get("correo"),
                telefono=st.session_state.datos_cliente.get("telefono"),
                nss=nss_str, semanas_cotizadas=semanas_int, sbc_promedio=sbc_float
            )
            if prospecto_guardado: 
                st.session_state.prospecto_id = prospecto_guardado.get("id")
                
            st.success("✅ Documento auditado con éxito. Revisa el análisis en la sección inferior.")
        except Ley97Error as e:
            st.session_state.resultado_extraccion = None
            st.error(f"⚠️ Restricción de Régimen: {e}")
        except Exception as e:
            st.session_state.resultado_extraccion = None
            st.error(f"Error al analizar el archivo: {e}")

def mostrar_resultado():
    if not st.session_state.resultado_extraccion:
        return
    st.divider()
    st.markdown('<div class="paso-badge">PASO 3</div>', unsafe_allow_html=True)
    st.subheader("Resumen General Detectado")
    
    res = st.session_state.resultado_extraccion
    
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-box">
            <div class="valor">Ley 73 ✓</div>
            <div class="etiqueta">Régimen Validado</div>
        </div>
        <div class="metric-box">
            <div class="valor">{int(float(res.get('semanas_cotizadas', 0)))}</div>
            <div class="etiqueta">Semanas Totales</div>
        </div>
        <div class="metric-box">
            <div class="valor">${float(res.get('sbc_promedio', 0)):,.2f}</div>
            <div class="etiqueta">SBC Promedio Actual</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_descarga_reporte():
    st.write("---")
    st.markdown("<h3 style='color: #134074; text-align: center; margin-bottom: 1.5rem;'>📈 Proyección Comparativa Avanzada (Desbloqueada)</h3>", unsafe_allow_html=True)
    
    res_ext = st.session_state.resultado_extraccion
    semanas_actuales = float(res_ext.get("semanas_cotizadas", 0))
    sbc_actual = float(res_ext.get("sbc_promedio", 0))
    nombre_prospecto = st.session_state.datos_cliente.get("nombre", "Asegurado")
    nss_prospecto = str(res_ext.get("nss", "No cargado"))
    
    try: uma_val = obtener_uma()
    except Exception: uma_val = 117.31

    st.markdown("<p style='font-size:0.95rem; font-weight:600;'>Ajusta los parámetros para simular tu plan de inversión:</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: 
        meses_m40 = st.slider("Meses de aportación en M40:", 12, 58, 58, step=1)
    with c2: 
        pago_mensual_m40 = st.slider("Monto mensual aproximado a aportar ($):", 3000, 15000, 5000, step=500)

    # ESCENARIO 1: RETIRO TRADICIONAL INERCIAL
    escenario_normal = calcular_escenario(
        sbc_promedio=sbc_actual, semanas=semanas_actuales, edad=60, uma=uma_val,
        tipo_asignacion="asistencia", salario_modalidad_40=sbc_actual, meses_modalidad_40=1, aplicar_fox=True
    )
    pension_normal = escenario_normal["pension"]["pension_final_mensual"]

    # ESCENARIO 2: RETIRO ESTRATÉGICO CON APORTACIONES VOLUNTARIAS
    tasa_vigente = 0.14438
    salario_diario_propuesto = pago_mensual_m40 / (30.4 * tasa_vigente)
    
    semanas_ganadas = meses_m40 * 4.345
    semanas_totales_m40 = semanas_actuales + semanas_ganadas

    escenario_m40_base = calcular_escenario(
        sbc_promedio=sbc_actual, semanas=semanas_totales_m40, edad=60, uma=uma_val,
        tipo_asignacion="asistencia", salario_modalidad_40=salario_diario_propuesto, meses_modalidad_40=meses_m40, aplicar_fox=True
    )
    salario_m40_aplicado = escenario_m40_base["modalidad_40"]["salario"]["sbc_aplicado"]
    
    sbc_ponderado = BlackBox_calcular_sbc_ponderado(sbc_actual, salario_m40_aplicado, meses_m40)
        
    escenario_m40_final = calcular_escenario(
        sbc_promedio=sbc_ponderado, semanas=semanas_totales_m40, edad=60, uma=uma_val,
        tipo_asignacion="asistencia", salario_modalidad_40=salario_diario_propuesto, meses_modalidad_40=meses_m40, aplicar_fox=True
    )
    
    pension_m40 = escenario_m40_final["pension"]["pension_final_mensual"]
    inversion_total_m40 = escenario_m40_final["modalidad_40"]["inversion"]["inversion_total"]
    ganancia_neta = max(0.0, pension_m40 - pension_normal)
    roi_meses = inversion_total_m40 / ganancia_neta if ganancia_neta > 0 else 0.0

    # TABLA COMPARATIVA CON CONTROL DE RENDIMIENTO TOTALMENTE ADAPTATIVO
    st.markdown("#### 🔄 Tabla Comparativa de Beneficios Financieros")
    
    tabla_comparativa = pd.DataFrame({
        "Factor de Análisis": [
            "Semanas Reconocidas", 
            "Salario Diario Promedio (SBC)", 
            "Aportación Mensual Requerida",
            "Inversión Total Acumulada",
            "Monto de Pensión Mensual",
            "INCREMENTO NETO GANADO"
        ],
        "Pensión Normal (Sin Estrategia)": [
            f"{int(semanas_actuales)} semanas",
            f"${sbc_actual:,.2f} MXN",
            "$0.00 MXN",
            "$0.00 MXN",
            f"${pension_normal:,.2f} MXN",
            "Base de Medición"
        ],
        "Plan Optimizado Pensión 40": [
            f"{int(semanas_totales_m40)} semanas",
            f"${sbc_ponderado:,.2f} MXN",
            f"${pago_mensual_m40:,.2f} MXN",
            f"${inversion_total_m40:,.2f} MXN",
            f"${pension_m40:,.2f} MXN",
            f"+${ganancia_neta:,.2f} MXN / mes"
        ]
    })
    
    st.dataframe(
        tabla_comparativa,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Factor de Análisis": st.column_config.TextColumn(width="medium"),
            "Pensión Normal (Sin Estrategia)": st.column_config.TextColumn(width="medium"),
            "Plan Optimizado Pensión 40": st.column_config.TextColumn(width="medium")
        }
    )

    # SECCIÓN CONTINÚA EN EL BLOQUE 3...
    # ============================================================
    # PENSION 40
    # app.py - CÓDIGO COMPLETO Y CORREGIDO (Bloque 3 de 3)
    # ============================================================

    # TARJETA EMPRESARIAL DE ROI
    st.markdown(f"""
    <div style="background-color: #E7F6ED; border-left: 5px solid #14804A; padding: 1rem; border-radius: 8px; margin-top: 1rem; margin-bottom: 1.5rem;">
        <h5 style='color: #14804A; margin-top:0; margin-bottom:0.2rem;'>💡 Dictamen Financiero de Viabilidad</h5>
        Al ejecutar esta estrategia, tu pensión mensual se eleva un excedente de <b>${ganancia_neta:,.2f} MXN netos mensuales</b>. 
        Recuperas tu capital total en un margen de <b>{roi_meses:.1f} meses</b> de cobros garantizados.
    </div>
    """, unsafe_allow_html=True)

    # CURVA DE CRECIMIENTO DE LA INVERSIÓN MENSUAL
    st.markdown("#### 📉 Curva del Flujo de Capital Invertido")
    tabla_mes = escenario_m40_final["modalidad_40"]["inversion"]["tabla_mensual"]
    if tabla_mes:
        df_chart = pd.DataFrame(tabla_mes)
        df_chart.rename(columns={"mes": "Mes", "inversion_acumulada": "Inversión Acumulada ($)"}, inplace=True)
        st.line_chart(df_chart, x="Mes", y="Inversión Acumulada ($)", use_container_width=True)

    # COMPILADOR SEGURO DE ARCHIVOS PDF OFICIALES
    if PDF_DISPONIBLE:
        try:
            # Diccionario empaquetado con datos cruzados de auditoría y simulador para ReportLab
            payload_simulacion = {
                "nombre": nombre_prospecto,
                "nss": nss_prospecto,
                "semanas_actuales": semanas_actuales,
                "semanas_finales": semanas_totales_m40,
                "sbc_actual": sbc_actual,
                "sbc_final": sbc_ponderado,
                "pension_actual": pension_normal,
                "pension_final": pension_m40,
                "inversion": inversion_total_m40,
                "roi": roi_meses
            }
            
            # Generar los bytes directos en memoria usando tu módulo de ReportLab
             pdf_bytes = generar_reporte_pdf(nombre_prospecto, escenario_normal, escenario_m40_final)
            
            st.write("---")
            st.markdown("<h4 style='text-align: center;'>📋 Descarga de Dictamen Certificado</h4>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Descargar Reporte Financiero Completo (PDF Ley 73)",
                data=pdf_bytes,
                file_name=f"Reporte_Financiero_M40_{nombre_prospecto.replace(' ', '_')}.pdf",
                mime="application/pdf",
                key="btn_descarga_pdf_real_hd"
            )
        except Exception as err_pdf:
            st.error(f"El motor matemático compiló correctamente, pero falló la generación del PDF: {err_pdf}")
    else:
        st.error("El módulo reporte_pdf.py no está disponible para descargas.")

    # LLAMADO A LA ACCIÓN AUTOMÁTICO DE ATENCIÓN AL CLIENTE
    st.markdown("""
    <div class="card" style="background-color: #F7F9FC; text-align: center; margin-top: 2rem; border: 1px dashed #1B6CA8;">
        <h4 style="color: #0B2545; margin-bottom: 0.3rem;">📬 ¿Tienes dudas o comentarios sobre tus escenarios?</h4>
        <p style="font-size: 0.9rem; margin-bottom: 0;">Escríbenos directamente a nuestro correo oficial de atención: <a href="mailto:contacto.pension40@gmail.com" style="font-weight:700; color:#1B6CA8;">contacto.pension40@gmail.com</a> y un consultor senior validará tu expediente.</p>
    </div>
    """, unsafe_allow_html=True)

def registrar_uso_promo():
    if not st.session_state.promo_validada or st.session_state.promo_uso_registrado:
        return
    codigo = st.session_state.codigo_promo
    if codigo:
        try:
            registrar_uso_promocion(codigo)
            st.session_state.promo_uso_registrado = True
        except Exception:
            pass

def mostrar_acceso_reporte():
    if not st.session_state.resultado_extraccion: 
        return
        
    st.divider()
    st.markdown("<h3 style='text-align: center;'>🔒 Desbloqueo de Reporte Avanzado</h3>", unsafe_allow_html=True)
    
    # CANDADO DE SEGURIDAD ESTRICTO: Solo abre si pagó o metió cupón válido
    if st.session_state.promo_validada or st.session_state.pago_confirmado:
        mostrar_descarga_reporte()
        return
        
    try: precio = obtener_precio_reporte()
    except Exception: precio = PRECIO_REPORTE_DEFAULT
        
    st.markdown(f"""
    <div class="card-azul" style="text-align: center; margin-bottom: 1rem;">
        <div class="precio">${precio:,.0f} MXN</div>
        <div class="precio-detalle" style="font-weight:600;">Reporte Avanzado de Simulación Ponderada</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("El acceso avanzado desbloqueará el análisis cruzado de incremento de cuantías, gráficas de rendimiento y descargas en formato PDF corporativo.")
    
    if st.button(f"💳 Obtener reporte por ${precio:,.0f} MXN", type="primary", key="btn_pago"):
        st.info("La pasarela de pago segura de Stripe/PayPal se conectará en la siguiente etapa.")

def validar_promocion():
    if st.session_state.promo_validada:
        return
    st.markdown('<div class="paso-badge">PASO 4</div>', unsafe_allow_html=True)
    st.subheader("Cupones o Códigos de Descuento")
    codigo = st.text_input("Ingresa tu código de cortesía corporativo:", placeholder="Ej: P40-PRUEBA").strip().upper()
    if st.button("Validar y Desbloquear Plataforma"):
        if codigo == "P40-PRUEBA":
            st.session_state.promo_validada = True
            st.success("🎉 Código promocional de prueba validado. Simulación completa liberada.")
            st.rerun()
        elif codigo:
            try:
                res = validar_codigo_promocional(codigo)
                if res.get("valido"):
                    st.session_state.promo_validada = True
                    st.session_state.codigo_promo = codigo
                    st.success("🎉 Código promocional validado.")
                    st.rerun()
                else:
                    st.error("El cupón ingresado expiró o no cuenta con usos disponibles.")
            except Exception:
                st.error("Error al validar el código promocional en el servidor.")

def main():
    mostrar_encabezado()
    mostrar_presentacion()
    capturar_datos()
    cargar_pdf()
    
    st.write("")
    if st.button("🚀 Iniciar Auditoría y Calcular Mi Pensión", type="primary", key="btn_calcular"):
        procesar_informacion()
        
    mostrar_resultado()
    if st.session_state.resultado_extraccion:
        validar_promocion()
        mostrar_acceso_reporte()
    mostrar_pie_de_pagina()

if __name__ == "__main__":
    main()
