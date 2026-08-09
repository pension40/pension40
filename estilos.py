# ============================================================
# PENSION 40
# estilos.py - Bloque 1 de 2 (CORRECCIÓN DE COMPILACIÓN SVG)
# ============================================================

import streamlit as st

AZUL_OSCURO = "#0B2545"
AZUL_PRINCIPAL = "#134074"
AZUL_MEDIO = "#1B6CA8"
AZUL_CLARO = "#EAF2FA"
VERDE_OK = "#14804A"
VERDE_CLARO = "#E7F6ED"
ROJO_ALERTA = "#B3261E"
ROJO_CLARO = "#FCEAEA"
GRIS_TEXTO = "#3B3B3B"
GRIS_SUAVE = "#6B7280"
GRIS_BORDE = "#E2E8F0"
GRIS_FONDO = "#F7F9FC"

# CORREGIDO: Se duplican las llaves de CSS nativo {{ }} que no son variables de Python 
# para que no corrompan el formato de Reporte o Interfaz.
LOGO_HORIZONTAL_SVG = f"""
<svg width="220" height="60" viewBox="0 0 440 120" xmlns="http://w3.org">
  <defs>
    <linearGradient id="escudoFondoH" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{AZUL_PRINCIPAL}" />
      <stop offset="100%" stop-color="{AZUL_OSCURO}" />
    </linearGradient>
  </defs>
  <g transform="translate(10, 10)">
    <path d="M50 7 L86 20 L86 48 C86 74 71 88 50 95 C29 88 14 74 14 48 L14 20 Z" fill="url(#escudoFondoH)" />
    <path d="M50 7 L86 20 L86 48 C86 74 71 88 50 95 C29 88 14 74 14 48 L14 20 Z" fill="none" stroke="{AZUL_MEDIO}" stroke-width="1.5" />
    <path d="M50 17 L77 27 L77 48 C77 68 66 79 50 85 C34 79 23 68 23 48 L23 27 Z" fill="none" stroke="{AZUL_CLARO}" stroke-width="1" opacity="0.35" />
    <text x="50" y="58" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="32" fill="#FFFFFF" letter-spacing="-1">40</text>
    <rect x="38" y="66" width="24" height="2.4" rx="1.2" fill="{VERDE_OK}" />
  </g>
  <text x="118" y="58" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="34" fill="{AZUL_OSCURO}" letter-spacing="-0.5">Pensión</text>
  <text x="118" y="58" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="34" fill="{AZUL_MEDIO}" letter-spacing="-0.5" dx="145">40</text>
  <text x="118" y="82" font-family="Helvetica, Arial, sans-serif" font-weight="500" font-size="13.5" fill="{GRIS_SUAVE}" letter-spacing="0.3">SIMULADOR LEY 73 · MODALIDAD 40</text>
</svg>
"""

LOGO_ICONO_SVG = f"""
<svg width="40" height="40" viewBox="0 0 200 200" xmlns="http://w3.org">
  <defs>
    <linearGradient id="escudoFondoIco" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{AZUL_PRINCIPAL}" />
      <stop offset="100%" stop-color="{AZUL_OSCURO}" />
    </linearGradient>
  </defs>
  <path d="M100 14 L172 40 L172 96 C172 148 142 176 100 190 C58 176 28 148 28 96 L28 40 Z" fill="url(#escudoFondoIco)" />
  <path d="M100 14 L172 40 L172 96 C172 148 142 176 100 190 C58 176 28 148 28 96 L28 40 Z" fill="none" stroke="{AZUL_MEDIO}" stroke-width="3" />
  <text x="100" y="115" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-weight="800" font-size="64" fill="#FFFFFF" letter-spacing="-2">40</text>
  <rect x="76" y="132" width="48" height="4" rx="2" fill="{VERDE_OK}" />
</svg>
"""

TITULO_PAGINA = "Pensión 40"
ICONO_PAGINA = "📊"
TEXTO_SUBTITULO = "Simulador financiero de pensión bajo Ley 73 del IMSS"
TEXTO_PIE_DE_PAGINA = 'Pensión 40 es un simulador financiero informativo. No sustituye ni garantiza resoluciones oficiales del IMSS. · <a href="https://pension40.mx" style="color:inherit;">www.pension40.mx</a>'
# ============================================================
# PENSION 40
# Módulo: estilos.py - Bloque 2 de 2 (ESCAPE DE COMPILACIÓN CSS)
# ============================================================

def _css() -> str:
    # CRÍTICO: Se duplican todas las llaves perimetrales de CSS de la hoja de estilos {{ }} 
    # para que Python entienda que es texto CSS nativo y NO variables dinámicas de código.
    return f"""
    <style>
    :root {{
        --azul-oscuro: {AZUL_OSCURO};
        --azul-principal: {AZUL_PRINCIPAL};
        --azul-medio: {AZUL_MEDIO};
        --azul-claro: {AZUL_CLARO};
        --azul-hover: #0F5A8F;
        --verde-ok: {VERDE_OK};
        --verde-claro: {VERDE_CLARO};
        --rojo-alerta: {ROJO_ALERTA};
        --rojo-claro: {ROJO_CLARO};
        --gris-texto: {GRIS_TEXTO};
        --gris-suave: {GRIS_SUAVE};
        --gris-borde: {GRIS_BORDE};
        --gris-fondo: {GRIS_FONDO};
    }}

    .main .block-container {{
        max-width: 720px;
        padding-top: 1rem;
        padding-bottom: 2.5rem;
    }}

    div[data-testid="stVerticalBlock"] > div {{
        gap: 0.4rem;
    }}

    h1, h2, h3 {{ margin-bottom: 0.3rem; }}

    .header-wrap {{
        text-align: center;
        margin-bottom: 0.8rem;
        padding-top: 0.2rem;
    }}

    .header-logo {{
        display: flex;
        justify-content: center;
        margin-bottom: 0.3rem;
    }}

    .titulo {{
        text-align: center;
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }}

    .subtitulo {{
        text-align: center;
        font-size: 0.9rem;
        color: var(--gris-suave);
        font-weight: 500;
        margin-bottom: 0;
    }}

    .linea-divisora {{
        height: 3px;
        width: 60px;
        background: linear-gradient(90deg, var(--azul-medio), var(--azul-oscuro));
        margin: 0.5rem auto 0.9rem auto;
        border-radius: 4px;
    }}

    .card {{
        padding: 0.9rem 1.1rem;
        border-radius: 10px;
        border: 1px solid var(--gris-borde);
        background: #FFFFFF;
        box-shadow: 0 1px 4px rgba(11, 37, 69, 0.05);
        margin-bottom: 0.7rem;
    }}

    .card h3, .card h4 {{
        color: var(--azul-oscuro);
        margin-top: 0;
        font-size: 1rem;
    }}

    .card-azul {{
        padding: 0.9rem 1.1rem;
        border-radius: 10px;
        background: var(--azul-claro);
        border: 1px solid rgba(27, 108, 168, 0.2);
        margin-bottom: 0.7rem;
    }}

    .card-compacta {{
        padding: 0.6rem 0.9rem;
        border-radius: 8px;
        border: 1px solid var(--gris-borde);
        background: var(--gris-fondo);
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }}

    .paso-badge {{
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
    }}

    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin: 0.5rem 0 0.6rem 0;
    }}

    .metric-box {{
        background: #FFFFFF;
        border: 1px solid var(--gris-borde);
        border-radius: 10px;
        padding: 0.6rem 0.4rem;
        text-align: center;
    }}

    .metric-box .valor {{
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        line-height: 1.15;
    }}

    .metric-box .etiqueta {{
        font-size: 0.68rem;
        color: var(--gris-suave);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        margin-top: 0.15rem;
    }}

    .precio {{
        text-align: center;
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin-bottom: 0.1rem;
    }}

    .precio-detalle {{
        text-align: center;
        font-size: 0.82rem;
        color: var(--gris-suave);
        margin-bottom: 0.4rem;
    }}

    .centrado {{ text-align: center; }}

    .beneficios {{
        list-style: none;
        padding-left: 0;
        margin: 0.4rem 0 0.1rem 0;
        columns: 2;
        column-gap: 1rem;
    }}

    .beneficios li {{
        padding: 0.15rem 0;
        color: var(--gris-texto);
        font-size: 0.82rem;
        break-inside: avoid;
    }}

    .beneficios li::before {{
        content: "✓";
        color: var(--verde-ok);
        font-weight: 800;
        margin-right: 0.4rem;
    }}

    .stButton > button {{
        width: 100%;
        min-height: 2.6rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.9rem;
        border: none;
        transition: transform 0.05s ease-in-out;
    }}

    .stButton > button:hover {{ transform: translateY(-1px); }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(90deg, var(--azul-medio), var(--azul-oscuro));
    }}

    div[data-testid="stDownloadButton"] > button {{
        width: 100%;
        min-height: 2.8rem;
        border-radius: 8px;
        font-weight: 700;
        background: linear-gradient(90deg, var(--verde-ok), #0F6B3C);
        color: white;
        border: none;
    }}

    .banner-precal {{
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 0.6rem 0 0.8rem 0;
        text-align: center;
    }}

    .banner-precal.ok {{
        background: linear-gradient(135deg, var(--verde-claro), #F3FBF6);
        border: 1.5px solid rgba(20, 128, 74, 0.35);
    }}

    .banner-precal.no {{
        background: linear-gradient(135deg, var(--rojo-claro), #FDF4F4);
        border: 1.5px solid rgba(179, 38, 30, 0.3);
    }}

    .banner-precal .icono {{ font-size: 1.6rem; }}

    .banner-precal .titulo-banner {{
        font-weight: 800;
        font-size: 1.05rem;
        margin: 0.25rem 0 0.1rem 0;
    }}

    .banner-precal.ok .titulo-banner {{ color: var(--verde-ok); }}
    .banner-precal.no .titulo-banner {{ color: var(--rojo-alerta); }}

    .banner-precal .subtexto {{
        font-size: 0.82rem;
        color: var(--gris-texto);
    }}

    .banner-precal .pension-grande {{
        font-size: 2rem;
        font-weight: 800;
        color: var(--azul-oscuro);
        margin: 0.3rem 0;
    }}

    .banner-desbloqueado {{
        background: linear-gradient(90deg, #E6F4EA, #EFFAF2);
        border: 1px solid rgba(30, 138, 76, 0.35);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        text-align: center;
        margin-bottom: 0.7rem;
    }}

    .banner-desbloqueado .icono {{ font-size: 1.5rem; }}

    .banner-desbloqueado .texto-principal {{
        font-weight: 800;
        color: var(--verde-ok);
        font-size: 1rem;
        margin: 0.2rem 0 0.05rem 0;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.3rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 2.4rem;
        font-weight: 600;
        font-size: 0.85rem;
    }}

    .footer {{
        text-align: center;
        font-size: 0.72rem;
        color: var(--gris-suave);
        margin-top: 1.8rem;
        line-height: 1.4;
    }}
    </style>
    """

def inyectar_estilos():
    st.markdown(_css(), unsafe_allow_html=True)

def mostrar_encabezado():
    st.markdown(f'<div class="header-wrap"><div class="header-logo">{LOGO_HORIZONTAL_SVG}</div><div class="linea-divisora"></div></div>', unsafe_allow_html=True)

def mostrar_pie_de_pagina():
    st.markdown(f'<div class="footer">{TEXTO_PIE_DE_PAGINA}</div>', unsafe_allow_html=True)
