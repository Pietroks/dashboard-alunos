import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import time
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO

from services.auth import inicializar_banco, verificar_credenciais
from services.google_sheets import carregar_planilha
from utils.tratamento import classificar_status

# 1. CONFIGURAÇÕES INICIAIS E ESTILIZAÇÃO DARK MODE
st.set_page_config(
    page_title="Dashboard Acadêmico | Uníntese",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Fundo Geral Dark */
        .stApp {
            background-color: #0F172A;
            color: #F8FAFC;
        }
        
        /* Sidebar Dark */
        [data-testid="stSidebar"] {
            background-color: #1E293B;
            border-right: 1px solid #334155;
        }
        [data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
        }
        
        /* Oculta o menu superior direito, botões de Fork/GitHub e cabeçalho padrão */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        [data-testid="stToolbar"] {display: none;}

        /* Oculta a barra de status e o rodapé 'Made with Streamlit' / 'Manage app' */
        footer {visibility: hidden;}
        [data-testid="stStatusWidget"] {display: none;}
        .stAppDeployButton {display: none;}
        ._profilePreview_gzau3_63 { display: none; }
        ._link_gzau3_10 { display: none; }
        
        /* Cards de Métricas Dark */
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
        
        /* Títulos e Cabeçalhos */
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
        
        /* Badges Dark */
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
        
        /* Botões Dark */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.15s ease;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES AUXILIARES E CARREGAMENTO DE DADOS
def renderizar_login() -> bool:
    inicializar_banco()
    
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["usuario_nome"] = ""

    if not st.session_state["autenticado"]:
        injetar_css_dark()
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background: #1E293B; padding: 32px; border-radius: 16px; border: 1px solid #334155; box-shadow: 0 8px 30px rgba(0,0,0,0.4); text-align: center;">
                <span style="font-size: 42px;">🎓</span>
                <h2 style="font-weight: 700; color: #F8FAFC; margin: 12px 0 4px 0;">Dashboard Acadêmico</h2>
                <p style="color: #94A3B8; font-size: 14px; margin-bottom: 24px;">Painel Institucional • Acesso Restrito</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("form_login"):
                usuario = st.text_input("Usuário", placeholder="ex: admin")
                senha = st.text_input("Senha", type="password", placeholder="••••••••")
                btn_entrar = st.form_submit_button("Entrar no Painel", width="stretch", type="primary")
                
                if btn_entrar:
                    nome = verificar_credenciais(usuario, senha)
                    if nome:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_nome"] = nome
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")
        return False
    return True

def obter_coluna(df: pd.DataFrame, opcoes: list) -> Optional[str]:
    for col in opcoes:
        if col in df.columns:
            return col
    return None

def calcular_faixa_etaria(df: pd.DataFrame) -> pd.DataFrame:
    col_nasc = obter_coluna(df, ["DataNascimento", "Data Nascimento", "Nascimento"])
    if not col_nasc or col_nasc not in df.columns:
        df["FaixaEtaria"] = "Não informado"
        return df

    serie_num = pd.to_numeric(df[col_nasc], errors="coerce")
    serie_valida = serie_num.where((serie_num >= 1) & (serie_num <= 50000))
    datas_num = pd.to_datetime(serie_valida, unit="D", origin="1899-12-30", errors="coerce")
    
    datas_str = pd.to_datetime(df[col_nasc].astype(str).replace("Não informado", None), errors="coerce", dayfirst=True)
    nascimento_dt = datas_num.combine_first(datas_str)
    
    df[col_nasc] = nascimento_dt.dt.strftime("%d/%m/%Y").fillna("Não informado")

    hoje = pd.Timestamp.now()
    idades = (hoje - nascimento_dt).dt.days // 365.25

    bins = [0, 17, 24, 34, 44, 54, 120]
    labels = ["Menor de 18", "18–24 anos", "25–34 anos", "35–44 anos", "45–54 anos", "55+ anos"]
    
    faixas = pd.cut(idades, bins=bins, labels=labels, right=True)
    df["FaixaEtaria"] = faixas.astype(str).replace(["nan", "NaN", "<NA>"], "Não informado")
    return df

@st.cache_data(ttl=300)
def carregar_dados() -> pd.DataFrame:
    tentativas = 2
    ultimo_erro = ""
    for i in range(tentativas):
        try:
            df = carregar_planilha()
            df = df.astype(str)
            df = df.replace(["", "nan", "None", "null", "NaN", "NAT"], "Não informado")
            df = df.replace(r"^\s*$", "Não informado", regex=True)
            
            df["StatusDashboard"] = df.apply(classificar_status, axis=1)
            df = calcular_faixa_etaria(df)
            
            logger.info(f"Dados carregados com sucesso: {len(df)} registros.")
            return df
        except Exception as e:
            ultimo_erro = str(e)
            logger.warning(f"Tentativa {i+1} falhou: {e}")
            if i < tentativas - 1:
                time.sleep(1)
            else:
                logger.error(f"Erro persistente ao carregar dados: {e}")
                st.error(f"❌ Erro de conexão com a planilha: {ultimo_erro}")
                return pd.DataFrame()

def aplicar_filtros(df: pd.DataFrame, filtros: Dict[str, list]) -> pd.DataFrame:
    for coluna, valores in filtros.items():
        if valores and coluna in df.columns:
            df = df[df[coluna].isin(valores)]
    return df

def aplicar_layout_dark(fig, height: int, show_legend: bool):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#94A3B8"),
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=show_legend,
        height=height,
        xaxis=dict(gridcolor="#334155", showline=False, color="#94A3B8"),
        yaxis=dict(gridcolor="#334155", showline=False, color="#94A3B8"),
        legend=dict(font=dict(color="#F1F5F9"))
    )
    return fig

def criar_grafico_barras(df: pd.DataFrame, x: str, title: str, orientation: str = "v", top_n: int = 15) -> px.bar:
    data = df[x].value_counts().head(top_n).reset_index()
    data.columns = [x, "Quantidade"]
    
    fig = px.bar(
        data, 
        x="Quantidade" if orientation == "h" else x, 
        y=x if orientation == "h" else "Quantidade",
        orientation=orientation,
        title=f"<b>{title}</b>",
        color_discrete_sequence=CORES_PALETTE,
        text_auto=True
    )
    fig.update_traces(
        textposition="outside",
        marker=dict(line=dict(width=0), opacity=0.9),
        textfont=dict(color="#F1F5F9")
    )
    return aplicar_layout_dark(fig, height=380 if orientation == "v" else 420, show_legend=False)

def criar_grafico_pizza(df: pd.DataFrame, names: str, title: str, height: int = 380) -> px.pie:
    data = df[names].value_counts().reset_index()
    data.columns = [names, "Quantidade"]
    
    fig = px.pie(
        data,
        names=names,
        values="Quantidade",
        title=f"<b>{title}</b>",
        color_discrete_sequence=CORES_PALETTE,
        hole=0.45
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Qtd: %{value}"
    )
    return aplicar_layout_dark(fig, height=height, show_legend=True)

def gerar_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Alunos")
    return output.getvalue()

# 3. SIDEBAR E FILTROS
def resetar_filtros():
    for k in list(st.session_state.keys()):
        if k.startswith("f_"):
            st.session_state[k] = []
        elif k == "busca_input":
            st.session_state["busca_input"] = ""

def renderizar_sidebar(df: pd.DataFrame):
    filtros = {}
    col_contrato = obter_coluna(df, ["Situacao do contrato", "Situação do contrato"])
    col_deficiencia = obter_coluna(df, ["Deficiência", "Deficiencia"])

    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 12px 0 16px 0; border-bottom: 1px solid #334155; margin-bottom: 16px;">
            <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Sessão Ativa</div>
            <div style="font-size: 16px; font-weight: 700; color: #F8FAFC; margin-top: 2px;">👤 {st.session_state.get('usuario_nome', 'Admin')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Sair do Sistema", width="stretch"):
            st.session_state["autenticado"] = False
            st.session_state["usuario_nome"] = ""
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 🔍 Busca Rápida")
        busca = st.text_input("Buscar Aluno", placeholder="Nome ou Matrícula...", key="busca_input", label_visibility="collapsed").strip()
        
        st.markdown("---")
        st.markdown("##### 🎛️ Filtros Avançados")
        
        colunas_candidatas = [
            ("Curso", "Curso"),
            ("Cidade", "Cidade"),
            ("Sexo", "Sexo"),
            ("Estado", "Estado"),
        ]
        
        if col_contrato:
            colunas_candidatas.append(("Situação do Contrato", col_contrato))
        if col_deficiencia:
            colunas_candidatas.append(("Deficiência", col_deficiencia))
        
        for label, coluna in colunas_candidatas:
            if coluna in df.columns:
                opcoes = sorted([str(x) for x in df[coluna].unique() if str(x) != "nan"])
                filtros[coluna] = st.multiselect(label, opcoes, placeholder="Todos", key=f"f_{coluna}")
        
        st.markdown("---")
        st.button("🔄 Limpar Filtros", on_click=resetar_filtros, width="stretch")
            
        if st.button("⚡ Atualizar Dados", width="stretch", type="secondary"):
            st.cache_data.clear()
            st.rerun()
            
    return busca, filtros

def renderizar_filtros_ativos(filtros: Dict[str, list], busca: str):
    filtros_selecionados = [f"<b>{col}</b>: {', '.join(map(str, vals))}" for col, vals in filtros.items() if vals]
    if busca:
        filtros_selecionados.insert(0, f"<b>Busca</b>: '{busca}'")
        
    if filtros_selecionados:
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38BDF8; padding: 10px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 20px;">
            📌 <b>Filtros Ativos:</b> {' &nbsp;|&nbsp; '.join(filtros_selecionados)}
        </div>
        """, unsafe_allow_html=True)

# 4. COMPONENTES VISUAIS PRINCIPAIS
def renderizar_metricas(df: pd.DataFrame):
    counts_status = df["StatusDashboard"].value_counts() if "StatusDashboard" in df.columns else pd.Series()
    
    metricas = {
        "total": len(df),
        "ATIVO": counts_status.get("ATIVO", 0),
        "TRANCADO": counts_status.get("TRANCADO", 0),
        "INATIVO": counts_status.get("INATIVO", 0),
        "DESISTENTE": counts_status.get("DESISTENTE", 0),
    }
    
    cols = st.columns(len(METRICAS_CONFIG))
    for i, config in enumerate(METRICAS_CONFIG):
        with cols[i]:
            cor = config["color"]
            bg = config["bg"]
            st.markdown(f"""
            <div class="metric-card-dark" style="border-top: 3px solid {cor};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; font-weight: 600; color: #94A3B8;">{config['label']}</span>
                    <span style="background: {bg}; color: {cor}; padding: 4px 8px; border-radius: 8px; font-size: 14px;">{config['icon']}</span>
                </div>
                <div style="font-size: 28px; font-weight: 700; color: #F8FAFC; margin-top: 10px;">
                    {metricas[config['key']]:,}
                </div>
            </div>
            """, unsafe_allow_html=True)

def renderizar_indicadores_academicos(df: pd.DataFrame):
    total = len(df)
    counts_status = df["StatusDashboard"].value_counts() if "StatusDashboard" in df.columns else pd.Series()
    
    indicadores = {
        "ATIVO": counts_status.get("ATIVO", 0),
        "TRANCADO": counts_status.get("TRANCADO", 0),
        "INATIVO": counts_status.get("INATIVO", 0),
        "DESISTENTE": counts_status.get("DESISTENTE", 0),
    }
    percentuais = {status: (qtd / total) * 100 if total > 0 else 0 for status, qtd in indicadores.items()}
    
    cols = st.columns(4)
    for i, status in enumerate(["ATIVO", "TRANCADO", "INATIVO", "DESISTENTE"]):
        with cols[i]:
            cor = CORES_STATUS[status]
            qtd = indicadores[status]
            pct = percentuais[status]
            st.markdown(f"""
            <div class="metric-card-dark" style="border-left: 4px solid {cor};">
                <div style="font-size: 12px; font-weight: 600; color: #94A3B8; text-transform: uppercase;">{status}</div>
                <div style="font-size: 24px; font-weight: 700; color: {cor}; margin-top: 4px;">{pct:.1f}%</div>
                <div style="font-size: 13px; color: #64748B; margin-top: 2px;">{qtd:,} estudantes</div>
            </div>
            """, unsafe_allow_html=True)

def renderizar_analise_situacao(df: pd.DataFrame):
    col_contrato = obter_coluna(df, ["Situacao do contrato", "Situação do contrato"])
    col_aluno = obter_coluna(df, ["Situacao do aluno", "Situação do aluno"])
    
    if not col_contrato:
        return
        
    situacoes_disponiveis = sorted(df[col_contrato].dropna().astype(str).str.strip().unique().tolist())
    situacao_selecionada = st.multiselect(
        "🔎 Filtrar situações contratuais nesta seção:",
        options=situacoes_disponiveis,
        placeholder="Todas as situações selecionadas...",
        key="analise_situacoes"
    )
    
    df_situacao = df[df[col_contrato].astype(str).isin(situacao_selecionada)].copy() if situacao_selecionada else df.copy()
    dados_situacao = df_situacao[col_contrato].astype(str).str.strip()
    resumo = dados_situacao.value_counts().reset_index()
    resumo.columns = ["Situação", "Quantidade"]
    total = resumo["Quantidade"].sum()
    resumo["Percentual"] = (resumo["Quantidade"] / total * 100) if total > 0 else 0
    
    col1, col2 = st.columns([3, 2])
    with col1:
        fig = px.bar(
            resumo, x="Situação", y="Quantidade", text="Quantidade",
            title="<b>Distribuição por Situação de Contrato</b>",
            color="Situação", color_discrete_sequence=CORES_PALETTE
        )
        fig.update_traces(textposition="outside", marker=dict(opacity=0.9), textfont=dict(color="#F1F5F9"))
        fig = aplicar_layout_dark(fig, height=360, show_legend=False)
        st.plotly_chart(fig, width="stretch")

    with col2:
        tabela_resumo = resumo.copy()
        tabela_resumo["Percentual"] = tabela_resumo["Percentual"].map(lambda x: f"{x:.1f}%")
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #94A3B8; margin-bottom: 8px;'>Tabela de Frequência</div>", unsafe_allow_html=True)
        st.dataframe(tabela_resumo, width="stretch", hide_index=True, height=330)

    if col_aluno and col_aluno in df_situacao.columns:
        st.markdown("<br><div style='font-size: 16px; font-weight: 600; color: #F1F5F9;'>🔄 Matriz Cruzada: Situação do Contrato × Situação do Aluno</div>", unsafe_allow_html=True)
        cruzamento_absoluto = pd.crosstab(df_situacao[col_contrato], df_situacao[col_aluno])
        cruzamento_percentual = pd.crosstab(df_situacao[col_contrato], df_situacao[col_aluno], normalize="index") * 100
        
        tab1, tab2 = st.tabs(["🔢 Valores Absolutos", "📈 Distribuição Percentual (%)"])
        with tab1:
            st.dataframe(cruzamento_absoluto, width="stretch")
        with tab2:
            st.dataframe(cruzamento_percentual.map(lambda x: f"{x:.1f}%"), width="stretch")

def criar_mapa_estados(df: pd.DataFrame):
    dados = df["Estado"].dropna().value_counts().reset_index()
    dados.columns = ["Estado", "Alunos"]
    
    estados = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
        "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
        "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
        "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
        "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
        "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
        "SE": "Sergipe", "TO": "Tocantins",
    }
    
    dados["EstadoNome"] = dados["Estado"].map(estados)
    dados = dados.dropna(subset=["EstadoNome"])
    
    fig = px.choropleth(
        dados,
        geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
        locations="EstadoNome",
        featureidkey="properties.name",
        color="Alunos",
        color_continuous_scale="Blues",
        scope="south america",
        hover_name="EstadoNome",
        hover_data={"Estado": True, "Alunos": True, "EstadoNome": False},
        labels={"Alunos": "Alunos", "Estado": "UF"},
        title="<b>Densidade Geográfica de Discentes</b>",
    )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94A3B8")
    )
    return fig

# 5. FUNÇÃO PRINCIPAL
def main():
    if not renderizar_login():
        return
        
    injetar_css_dark()
    
    with st.spinner("🔄 Carregando dados da planilha institucional..."):
        df = carregar_dados()
    
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível no momento.")
        if st.button("🔄 Tentar Novamente", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        return
        
    busca, filtros = renderizar_sidebar(df)
    df_filtrado = aplicar_filtros(df, filtros)
    
    if busca:
        col_nome = obter_coluna(df_filtrado, ["Nome", "Aluno"])
        col_matr = obter_coluna(df_filtrado, ["Matricula", "Matrícula"])
        
        cond_nome = df_filtrado[col_nome].astype(str).str.contains(busca, case=False, na=False) if col_nome else False
        cond_matr = df_filtrado[col_matr].astype(str).str.contains(busca, case=False, na=False) if col_matr else False
        df_filtrado = df_filtrado[cond_nome | cond_matr]
    
    # Cabeçalho Principal Dark Mode
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">🎓 Dashboard de Gestão Acadêmica</h1>
            <p style="font-size: 14px; color: #94A3B8; margin: 4px 0 0 0;">Monitoramento de discentes, retenção e perfil institucional</p>
        </div>
        <span class="custom-badge-dark">📊 {len(df_filtrado):,} discentes filtrados</span>
    </div>
    """, unsafe_allow_html=True)
    
    renderizar_filtros_ativos(filtros, busca)
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum aluno encontrado para o conjunto de filtros selecionado. Ajuste os seletores na barra lateral.")
        return
    
    renderizar_metricas(df_filtrado)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header-dark'>📈 Indicadores Acadêmicos de Retenção</div>", unsafe_allow_html=True)
    renderizar_indicadores_academicos(df_filtrado)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header-dark'>🔎 Análise Detalhada de Situação Contratual</div>", unsafe_allow_html=True)
    renderizar_analise_situacao(df_filtrado)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header-dark'>📚 Análise de Cursos, Turmas e Ingresso</div>", unsafe_allow_html=True)
    ca1, ca2, ca3 = st.columns(3)
    if "Curso" in df_filtrado.columns:
        ca1.plotly_chart(criar_grafico_barras(df_filtrado, "Curso", "Alunos por Curso", "h"), width="stretch")
    if "Turma" in df_filtrado.columns:
        ca2.plotly_chart(criar_grafico_barras(df_filtrado, "Turma", "Distribuição por Turma"), width="stretch")
    col_ingresso = obter_coluna(df_filtrado, ["FormaIngresso", "Forma de Ingresso"])
    if col_ingresso:
        ca3.plotly_chart(criar_grafico_pizza(df_filtrado, col_ingresso, "Forma de Ingresso"), width="stretch")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header-dark'>👤 Perfil Demográfico e Acessibilidade</div>", unsafe_allow_html=True)
    cd1, cd2 = st.columns(2)
    if "FaixaEtaria" in df_filtrado.columns:
        cd1.plotly_chart(criar_grafico_barras(df_filtrado, "FaixaEtaria", "Distribuição por Faixa Etária"), width="stretch")
    
    col_deficiencia = obter_coluna(df_filtrado, ["Deficiência", "Deficiencia"])
    if col_deficiencia:
        cd2.plotly_chart(criar_grafico_pizza(df_filtrado, col_deficiencia, "Perfil de Acessibilidade"), width="stretch")
        
    cp1, cp2 = st.columns(2)
    if "Sexo" in df_filtrado.columns:
        cp1.plotly_chart(criar_grafico_pizza(df_filtrado, "Sexo", "Distribuição por Sexo"), width="stretch")
    col_raca = obter_coluna(df_filtrado, ["CorRaca", "Cor/Raça"])
    if col_raca:
        cp2.plotly_chart(criar_grafico_barras(df_filtrado, col_raca, "Distribuição por Cor/Raça"), width="stretch")
        
    cp3, cp4 = st.columns(2)
    if "Escolaridade" in df_filtrado.columns:
        cp3.plotly_chart(criar_grafico_barras(df_filtrado, "Escolaridade", "Nível de Escolaridade", "h"), width="stretch")
    col_prof = obter_coluna(df_filtrado, ["Profissao", "Profissão"])
    if col_prof:
        cp4.plotly_chart(criar_grafico_barras(df_filtrado, col_prof, "Top Profissões Declaradas", "h", top_n=10), width="stretch")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header-dark'>🗺️ Distribuição Geográfica Nacional</div>", unsafe_allow_html=True)
    if "Estado" in df_filtrado.columns and not df_filtrado["Estado"].replace("Não informado", None).dropna().empty:
        fig_mapa = criar_mapa_estados(df_filtrado)
        st.plotly_chart(fig_mapa, width="stretch")
    else:
        st.info("Nenhum dado geográfico disponível para exibir o mapa.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header-dark'>📋 Registros Detalhados & Exportação</div>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Exportar Relatório CSV", data=csv, file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.csv", mime="text/csv", width="stretch")
        
    with btn_col2:
        with st.spinner("Gerando arquivo Excel..."):
            dados_excel = gerar_excel(df_filtrado)
        st.download_button("📊 Exportar Relatório Excel (.xlsx)", data=dados_excel, file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        
    st.dataframe(df_filtrado, width="stretch", height=420)

if __name__ == "__main__":
    main()