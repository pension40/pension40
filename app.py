# ============================================================
# PENSION 40
# app.py - Aplicación Principal Corregida (Bloque 1 de 3)
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

# MÓDULOS DEL PROYECTO
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

try:
    from extractor import analizar_pdf_streamlit, Ley97Error, SemanasInsuficientesError, ExtractorPensionError
    EXTRACTOR_DISPONIBLE = True
except ImportError:
    EXTRACTOR_DISPONIBLE = False

from estilos import inyectar_estilos, mostrar_encabezado, mostrar_pie_de_pagina

# INYECTAR ESTILOS INMEDIATAMENTE DESPUÉS DE LAS IMPORTACIONES
inyectar_estilos()

PRECIO_REPORTE_DEFAULT = 249

# INITIALIZE SESSION STATE SI NO EXISTE
valores_iniciales = {
    "admin_autenticado": False, "pdf": None, "datos_cliente": {}, "resultado_extraccion": None,
    "resultado_calculo": None, "promo_validada": False, "codigo_promo": "", "pago_confirmado": False,
    "reporte_generado": False, "prospecto_id": None, "promo_uso_registrado": False,
    "edad_retiro": 60, "tipo_asignacion": "ninguna", "meses_m40": 58, "pdf_reporte_bytes": None,
    "tiene_hijos": False, "proyeccion": None, "precalificacion": None, "modo_captura": "pdf",
    "datos_manuales_validos": False, "pago_mensual_m40": 5000.0, "salario_modalidad_40": None
}

for clave, valor in valores_iniciales.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor

# ============================================================
# COMPONENTES DE ENTRADA Y FORMULARIOS
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
# app.py - Aplicación Principal Corregida (Bloque 2 de 3)
# ============================================================

# ============================================================
# PENSION 40
# app.py - Aplicación Principal Corregida (Bloque 2 de 3)
# ============================================================

def validar_datos():
    errores = []
    datos = st.session_state.datos_cliente
    if not datos.get("nombre"): errores.append("Por favor, escribe tu nombre completo.")
    if not datos.get("correo"): errores.append("Por favor, ingresa tu correo electrónico.")
    if not datos.get("telefono"): errores.append("Por favor, introduce tu número de WhatsApp.")
    if st.session_state.pdf is None: errores.append("Es necesario subir tu archivo PDF de Semanas Cotizadas.")
    return errores

def procesar_informacion():
    errores = validar_datos()
    if errores:
        for err in errores: st.error(err)
        return
        
    with st.spinner("Procesando historial y auditando derechos Ley 73..."):
        try:
            resultado = analizar_pdf_streamlit(st.session_state.pdf)
            st.session_state.resultado_extraccion = resultado
            
            # Sanitizar tipos de datos para evitar errores de persistencia en Supabase
            semanas_int = int(float(resultado.get("semanas_cotizadas", 0)))
            sbc_float = float(resultado.get("sbc_promedio", 0.0))
            nss_data = resultado.get("nss", "")
            nss_str = nss_data if isinstance(nss_data, list) else str(nss_data)
            
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
            st.error(f"⚠️ Restricción de Régimen: {e}")
        except Exception as e:
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
            <div class="valor">{{int(float(res.get('semanas_cotizadas', 0)))}}</div>
            <div class="etiqueta">Semanas Totales</div>
        </div>
        <div class="metric-box">
            <div class="valor">${{float(res.get('sbc_promedio', 0)):,.2f}}</div>
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
    
    try: uma_val = obtener_uma()
    except Exception: uma_val = 117.31

    # CONTROLES INTERACTIVOS DE NEGOCIACIÓN COMERCIAL
    st.markdown("<p style='font-size:0.95rem; font-weight:600;'>Ajusta los parámetros para simular tu plan de inversión:</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: 
        meses_m40 = st.slider("Meses de aportación en M40:", 12, 58, 58, step=1)
    with c2: 
        pago_mensual_m40 = st.slider("Monto mensual aproximado a aportar ($):", 3000, 12000, 5000, step=500)

    # CÁLCULOS CRUZADOS DE AMBOS ESCENARIOS
    escenario_normal = calcular_escenario(
        sbc_promedio=sbc_actual, semanas=semanas_actuales, edad=60, uma=uma_val,
        tipo_asignacion="asistencia", salario_modalidad_40=sbc_actual, meses_modalidad_40=1, aplicar_fox=True
    )
    pension_normal = escenario_normal["pension"]["pension_final_mensual"]

    # Derivamos el salario diario aproximado basado en el pago mensual elegido usando la tasa del año actual (14.438%)
    tasa_2026 = 0.14438
    salario_diario_propuesto = pago_mensual_m40 / (30.4 * tasa_2026)
    
    # Al aportar X meses, ganamos semanas adicionales (X meses * 4.345 semanas promedio por mes)
    semanas_ganadas = meses_m40 * 4.345
    semanas_totales_m40 = semanas_actuales + semanas_ganadas

    escenario_m40 = calcular_escenario(
        sbc_promedio=sbc_actual, semanas=semanas_totales_m40, edad=60, uma=uma_val,
        tipo_asignacion="asistencia", salario_modalidad_40=salario_diario_propuesto, meses_modalidad_40=meses_m40, aplicar_fox=True
    )
    
    if meses_m40 >= 54:
        sbc_ponderado = escenario_m40["modalidad_40"]["salario"]["sbc_aplicado"]
    else:
        porcentaje_reemplazo = (meses_m40 * 30.4) / 1750
        sbc_ponderado = (sbc_actual * (1 - porcentaje_reemplazo)) + (escenario_m40["modalidad_40"]["salario"]["sbc_aplicado"] * porcentaje_reemplazo)
        
    escenario_m40_recalc = calcular_escenario(
        sbc_promedio=sbc_ponderado, semanas=semanas_totales_m40, edad=60, uma=uma_val,
        tipo_asignacion="asistencia", salario_modalidad_40=salario_diario_propuesto, meses_modalidad_40=meses_m40, aplicar_fox=True
    )
    
    pension_m40 = escenario_m40_recalc["pension"]["pension_final_mensual"]
    inversion_total_m40 = escenario_m40_recalc["modalidad_40"]["inversion"]["inversion_total"]
    ganancia_neta = max(0.0, pension_m40 - pension_normal)
    roi_meses = inversion_total_m40 / ganancia_neta if ganancia_neta > 0 else 0.0

    # TABLA COMPARATIVA DIRECTA CON CORRECCIÓN DE LAYOUT RESPONSIVO
    st.markdown("#### 🔄 Tabla Comparativa de Beneficios")
    
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
            "Base"
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
    
    # RENDERIZADOR OPTIMIZADO: Elimina el colapso vertical y fuerza un ancho completo responsivo
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

    # TARJETA DE ACCIÓN COMERCIAL (ROI)
    st.markdown(f"""
    <div style="background-color: #E7F6ED; border-left: 5px solid #14804A; padding: 1rem; border-radius: 8px; margin-top: 1rem; margin-bottom: 1.5rem;">
        <h5 style='color: #14804A; margin-top:0; margin-bottom:0.2rem;'>💡 Dictamen Financiero de Viabilidad</h5>
        Al invertir en este plan, tu pensión aumenta <b>${ganancia_neta:,.2f} MXN cada mes</b>. 
        Recuperas toda tu inversión acumulada en tan solo <b>{roi_meses:.1f} meses</b> de haber iniciado tus cobros del IMSS.
    </div>
    """, unsafe_allow_html=True)
    # CONTINÚA EN EL BLOQUE 3...
    # ============================================================
    # PENSION 40
    # app.py - Aplicación Principal Corregida (Bloque 3 de 3)
    # ============================================================
    
    # GRÁFICA INTERACTIVA DEL FLUJO DE CAJA ACUMULADO
    st.markdown("#### 📉 Curva de Crecimiento de la Inversión")
    tabla_mes = escenario_m40_recalc["modalidad_40"]["inversion"]["tabla_mensual"]
    if tabla_mes:
        df_chart = pd.DataFrame(tabla_mes)
        df_chart.rename(columns={"mes": "Mes", "inversion_acumulada": "Inversión Acumulada ($)"}, inplace=True)
        st.line_chart(df_chart, x="Mes", y="Inversión Acumulada ($)", use_container_width=True)

    # CONSTANCIA DIGITAL EJECUTIVA PARA DESCARGA
    reporte_txt = f"""========================================================================
                  PENSIÓN 40 - REPORTE EJECUTIVO DE RETIRO
========================================================================
EMISIÓN: {datetime.now().strftime('%d/%m/%Y')}
CLIENTE: {st.session_state.datos_cliente.get('nombre', 'Asegurado')}
------------------------------------------------------------------------
1. ESCENARIO INERCIAL (SIN INVERSIÓN):
- Semanas Cotizadas: {int(semanas_actuales)}
- Salario Promedio Histórico: ${sbc_actual:,.2f} MXN
- Pensión Mensual Estimada: ${pension_normal:,.2f} MXN

2. ESCENARIO OPTIMIZADO (CON PLAN PENSIÓN 40):
- Duración de Aportaciones en M40: {meses_m40} Meses
- Semanas Totales Alcanzadas: {int(semanas_totales_m40)}
- Salario Promedio Ponderado Final: ${sbc_ponderado:,.2f} MXN
- Inversión Total Acumulada en M40: ${inversion_total_m40:,.2f} MXN
- MONTO DE PENSIÓN ESTIMADA FINAL: ${pension_m40:,.2f} MXN / mes

3. ANÁLISIS DE RETORNO (ROI):
- Ganancia Financiera Neta: +${ganancia_neta:,.2f} MXN adicionales mensuales
- Tiempo de Recuperación de Inversión: {roi_meses:.1f} Meses
========================================================================
¿Tienes dudas sobre tu estrategia?
Envía un correo directamente a: contacto.pension40@gmail.com
========================================================================
"""
    st.download_button(
        label="📥 Descargar esta Proyección Estratégica en mi Dispositivo", 
        data=reporte_txt, 
        file_name=f"Estrategia_M40_{st.session_state.datos_cliente.get('nombre', 'Asegurado').replace(' ', '_')}.txt",
        mime="text/plain"
    )
    
    # CTA DE ATENCIÓN DIRECTA AL FINAL DEL REPORTE
    st.markdown("""
    <div class="card" style="background-color: #F7F9FC; text-align: center; margin-top: 2rem; border: 1px dashed #1B6CA8;">
        <h4 style="color: #0B2545; margin-bottom: 0.3rem;">📬 ¿Tienes dudas o comentarios sobre tus escenarios?</h4>
        <p style="font-size: 0.9rem; margin-bottom: 0;">Escríbenos directamente a nuestro correo oficial de atención: <a href="mailto:contacto.pension40@gmail.com" style="font-weight:700; color:#1B6CA8;">contacto.pension40@gmail.com</a> y un consultor senior validará tu expediente.</p>
    </div>
    """, unsafe_allow_html=True)

def mostrar_acceso_reporte():
    if not st.session_state.resultado_extraccion: return
    if st.session_state.promo_validada:
        mostrar_descarga_reporte()
        return
        
    # Si no tiene código de descuento, mostramos la opción de compra normal
    mostrar_descarga_reporte()

def validar_promocion():
    st.markdown('<div class="paso-badge">PASO 4</div>', unsafe_allow_html=True)
    st.subheader("Códigos Promocionales o Cupones")
    codigo = st.text_input("Ingresa tu código de cortesía si cuentas con uno:", placeholder="P40-PRUEBA").strip().upper()
    if st.button("Validar y Desbloquear Reporte Financiero"):
        if codigo == "P40-PRUEBA":
            st.session_state.promo_validada = True
            st.success("🎉 Código de prueba validado con éxito. Se ha activado la simulación completa.")
            st.rerun()
        elif codigo:
            try:
                res = validar_codigo_promocional(codigo)
                if res.get("valido"):
                    st.session_state.promo_validada = True
                    st.session_state.codigo_promo = codigo
                    st.success("🎉 Cupón corporativo validado.")
                    st.rerun()
                else:
                    st.error("El cupón ingresado expiró o es inválido.")
            except Exception:
                st.error("No se pudo conectar al servidor para validar el cupón.")

def main():
    mostrar_encabezado()
    mostrar_presentacion()
    capturar_datos()
    cargar_pdf()
    
    st.write("")
    if st.button("🚀 Iniciar Auditoría y Calcular Mi Pensión", type="primary"):
        procesar_informacion()
        
    mostrar_resultado()
    if st.session_state.resultado_extraccion:
        validar_promocion()
        mostrar_acceso_reporte()
    mostrar_pie_de_pagina()

if __name__ == "__main__":
    main()
