import streamlit as st

# Paleta de Cores e Identidade Visual (Dark Mode)
CORES_STATUS = {
    "ATIVO": "#10B981",       # Emerald Green
    "TRANCADO": "#F59E0B",     # Amber Orange
    "INATIVO": "#EF4444",      # Rose Red
    "DESISTENTE": "#94A3B8"    # Slate Gray
}

CORES_PALETTE = ["#38BDF8", "#34D399", "#A78BFA", "#FBBF24", "#F472B6", "#22D3EE", "#94A3B8"]

METRICAS_CONFIG = [
    {"key": "total", "label": "Total de Alunos", "icon": "👥", "color": "#38BDF8", "bg": "rgba(56, 189, 248, 0.12)"},
    {"key": "ATIVO", "label": "Alunos Ativos", "icon": "✅", "color": CORES_STATUS["ATIVO"], "bg": "rgba(16, 185, 129, 0.12)"},
    {"key": "TRANCADO", "label": "Trancados", "icon": "⏸️", "color": CORES_STATUS["TRANCADO"], "bg": "rgba(245, 158, 11, 0.12)"},
    {"key": "INATIVO", "label": "Inativos", "icon": "❌", "color": CORES_STATUS["INATIVO"], "bg": "rgba(239, 68, 68, 0.12)"},
    {"key": "DESISTENTE", "label": "Desistentes", "icon": "🚫", "color": CORES_STATUS["DESISTENTE"], "bg": "rgba(148, 163, 184, 0.12)"},
]

def injetar_css_dark():
    """Injeta as regras de CSS para estilização completa no modo Dark com suporte a reabertura de sidebar."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* 1. Header Transparente: permite que o botão de abrir/fechar sidebar (stSidebarCollapsedControl) fique visível */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100 !important;
        }

        /* Mantém o botão de toggle/reabertura da sidebar visível e estilizado em Dark Mode */
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            color: #F8FAFC !important;
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            margin: 8px !important;
        }
        [data-testid="stSidebarCollapsedControl"]:hover {
            border-color: #38BDF8 !important;
            color: #38BDF8 !important;
        }

        /* 2. Oculta apenas menus de configuração, deploy e fork */
        #MainMenu {visibility: hidden !important; display: none !important;}
        .stAppDeployButton {display: none !important;}
        footer {visibility: hidden !important; display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}

        /* Oculta badges e avatar do Streamlit Community Cloud */
        [data-testid="appCreatorAvatar"],
        div[class*="_profileContainer_"],
        div[class*="_profilePreview_"],
        div[class*="_viewerBadge_"],
        div[class*="_profileBadge_"],
        div[class*="_floatingActions_"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        /* 3. Espaçamento da página */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* 4. Fundo Geral Dark */
        .stApp {
            background-color: #0F172A;
            color: #F8FAFC;
        }
        
        /* 5. Sidebar Dark */
        [data-testid="stSidebar"] {
            background-color: #1E293B;
            border-right: 1px solid #334155;
        }
        [data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
        }

        /* 6. Campos de Entrada com Alto Contraste */
        div[data-baseweb="input"] input {
            color: #F8FAFC !important;
            background-color: #0F172A !important;
        }
        
        /* 7. Cards de Métricas Dark */
        .metric-card-dark {
            background: #1E293B;
            padding: 20px;
            border-radius: 14px;
            border: 1px solid #334155;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            transition: all 0.2s ease-in-out;
            height: 100%;
        }
        .metric-card-dark:hover {
            transform: translateY(-2px);
            border-color: #475569;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        }
        
        /* 8. Cabeçalhos de Seção */
        .section-header-dark {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 28px;
            margin-bottom: 16px;
            font-size: 20px;
            font-weight: 700;
            color: #F8FAFC;
        }
        
        /* 9. Badges */
        .custom-badge-dark {
            background: #334155;
            color: #38BDF8;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid #475569;
            display: inline-flex;
            align-items: center;
        }
        
        /* 10. Botões */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.15s ease;
        }
    </style>
    """, unsafe_allow_html=True)