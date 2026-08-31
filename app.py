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

# 1. CONFIGURAÇÕES INICIAIS E CONSTANTES
st.set_page_config(page_title="Dashboard Acadêmico", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORES_STATUS = {"ATIVO": "#22C55E", "TRANCADO": "#F59E0B", "INATIVO": "#EF4444", "DESISTENTE": "#6B7280"}
CORES_PALETTE = px.colors.qualitative.Safe

METRICAS_CONFIG = [
    {"key": "total", "label": "Total de Alunos", "icon": "👥", "color": "#000000"},
    {"key": "ATIVO", "label": "Ativos", "icon": "✅", "color": CORES_STATUS["ATIVO"]},
    {"key": "TRANCADO", "label": "Trancados", "icon": "⏸️", "color": CORES_STATUS["TRANCADO"]},
    {"key": "INATIVO", "label": "Inativos", "icon": "❌", "color": CORES_STATUS["INATIVO"]},
    {"key": "DESISTENTE", "label": "Desistentes", "icon": "🚫", "color": CORES_STATUS["DESISTENTE"]},
]

# 2. FUNÇÕES AUXILIARES, TRATAMENTO E CACHE
def renderizar_login() -> bool:
    inicializar_banco()
    
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["usuario_nome"] = ""

    if not st.session_state["autenticado"]:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("### 🎓 Acesso ao Dashboard Acadêmico")
            
            with st.form("form_login"):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                btn_entrar = st.form_submit_button("Entrar", width="stretch")
                
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

    # 1. Filtra apenas números válidos de série do Excel (entre 1 e 50.000 para evitar anos além de 2030)
    serie_num = pd.to_numeric(df[col_nasc], errors="coerce")
    serie_valida = serie_num.where((serie_num >= 1) & (serie_num <= 50000))
    datas_num = pd.to_datetime(serie_valida, unit="D", origin="1899-12-30", errors="coerce")
    
    # 2. Converte textos de data (ex: "20/12/2002") com formato flexível
    datas_str = pd.to_datetime(df[col_nasc].astype(str).replace("Não informado", None), errors="coerce", dayfirst=True)
    
    # 3. Une as duas conversões
    nascimento_dt = datas_num.combine_first(datas_str)
    
    # 4. Formata a coluna original de DataNascimento para texto legível (DD/MM/AAAA)
    # Isso elimina os números brutos (ex: 37610) e resolve o erro do PyArrow na tabela
    df[col_nasc] = nascimento_dt.dt.strftime("%d/%m/%Y").fillna("Não informado")

    # 5. Calcula as idades e classifica em faixas etárias
    hoje = pd.Timestamp.now()
    idades = (hoje - nascimento_dt).dt.days // 365.25

    bins = [0, 17, 24, 34, 44, 54, 120]
    labels = ["Menor de 18", "18–24 anos", "25–34 anos", "35–44 anos", "45–54 anos", "55+ anos"]
    
    faixas = pd.cut(idades, bins=bins, labels=labels, right=True)
    df["FaixaEtaria"] = faixas.astype(str).replace(["nan", "NaN", "<NA>"], "Não informado")
    return df

@st.cache_data(ttl=300)
def carregar_dados() -> pd.DataFrame:
    tentativas = 3
    for i in range(tentativas):
        try:
            df = carregar_planilha()
            
            # Padroniza tipos para evitar erros de tipagem mista no PyArrow
            df = df.astype(str)
            df = df.replace(["", "nan", "None", "null", "NaN", "NAT"], "Não informado")
            df = df.replace(r"^\s*$", "Não informado", regex=True)
            
            # Tratamentos e classificações
            df["StatusDashboard"] = df.apply(classificar_status, axis=1)
            df = calcular_faixa_etaria(df)
            
            logger.info(f"Dados carregados com sucesso: {len(df)} registros.")
            return df
        except Exception as e:
            logger.warning(f"Tentativa {i+1} falhou: {e}")
            if i < tentativas - 1:
                time.sleep(2)
            else:
                logger.error(f"Erro persistente ao carregar dados: {e}")
                st.error("❌ Falha temporária ao conectar com a planilha do Google Sheets. Clique no botão de atualização abaixo para tentar novamente.")
                return pd.DataFrame()

def aplicar_filtros(df: pd.DataFrame, filtros: Dict[str, list]) -> pd.DataFrame:
    for coluna, valores in filtros.items():
        if valores and coluna in df.columns:
            df = df[df[coluna].isin(valores)]
    return df

def aplicar_layout_padrao(fig, height: int, show_legend: bool):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=20, r=20, t=40, b=20), showlegend=show_legend, height=height
    )
    return fig

def criar_grafico_barras(df: pd.DataFrame, x: str, title: str, orientation: str = "v", top_n: int = 15) -> px.bar:
    data = df[x].value_counts().head(top_n).reset_index()
    data.columns = [x, "Quantidade"]
    
    fig = px.bar(
        data, 
        x="Quantidade" if orientation == "h" else x, 
        y=x if orientation == "h" else "Quantidade",
        orientation=orientation, title=title, color_discrete_sequence=CORES_PALETTE, text_auto=True
    )
    fig.update_traces(textposition="outside", marker=dict(line=dict(width=0.5, color="white")))
    return aplicar_layout_padrao(fig, height=400 if orientation == "v" else 450, show_legend=False)

def criar_grafico_pizza(df: pd.DataFrame, names: str, title: str, height: int = 400) -> px.pie:
    data = df[names].value_counts().reset_index()
    data.columns = [names, "Quantidade"]
    
    fig = px.pie(data, names=names, values="Quantidade", title=title, color_discrete_sequence=CORES_PALETTE, hole=0.3)
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="<b>%{label}</b><br>Qtd: %{value}")
    return aplicar_layout_padrao(fig, height, show_legend=True)

def gerar_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Alunos")
    return output.getvalue()

# 3. CALLBACKS E COMPONENTES VISUAIS
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
        st.markdown(f"👤 **Usuário:** {st.session_state.get('usuario_nome', 'Admin')}")
        if st.button("🚪 Sair", width="stretch"):
            st.session_state["autenticado"] = False
            st.session_state["usuario_nome"] = ""
            st.rerun()
        st.markdown("---")
        
        st.markdown("### 🔍 Busca Direta")
        busca = st.text_input("Pesquisar por Nome ou Matrícula", placeholder="Digite algo...", key="busca_input").strip()
        
        st.markdown("---")
        st.markdown("### 🎛️ Filtros Avançados")
        
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
                filtros[coluna] = st.multiselect(label, opcoes, placeholder="Selecione...", key=f"f_{coluna}")
        
        st.markdown("---")
        st.button("🔄 Limpar todos os filtros", on_click=resetar_filtros, width="stretch")
            
        if st.button("⚡ Forçar Atualização dos Dados", width="stretch"):
            st.cache_data.clear()
            st.rerun()
            
    return busca, filtros

def renderizar_filtros_ativos(filtros: Dict[str, list], busca: str):
    filtros_selecionados = [f"**{col}**: {', '.join(map(str, vals))}" for col, vals in filtros.items() if vals]
    if busca:
        filtros_selecionados.insert(0, f"**Busca**: '{busca}'")
        
    if filtros_selecionados:
        st.info("📌 **Filtros Ativos:** " + " | ".join(filtros_selecionados))

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
            st.markdown(f"""
            <div style="background: white; padding: 18px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); text-align: center; border-left: 4px solid {cor}; height: 100%;">
                <div style="font-size: 13px; color: #6B7280; font-weight: 500;">{config['icon']} {config['label']}</div>
                <div style="font-size: 28px; font-weight: 700; color: {cor}; margin-top: 6px;">{metricas[config['key']]:,}</div>
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
            st.markdown(
                f"""
                <div style="background: white; padding: 16px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border-left: 4px solid {cor}; text-align: center;">
                    <div style="font-size: 13px; color: #6B7280; font-weight: 500;">{status}</div>
                    <div style="font-size: 26px; font-weight: 700; color: {cor}; margin-top: 4px;">{pct:.1f}%</div>
                    <div style="font-size: 12px; color: #6B7280; margin-top: 2px;">{qtd:,} alunos</div>
                </div>
                """,
                unsafe_allow_html=True
            )

def renderizar_analise_situacao(df: pd.DataFrame):
    col_contrato = obter_coluna(df, ["Situacao do contrato", "Situação do contrato"])
    col_aluno = obter_coluna(df, ["Situacao do aluno", "Situação do aluno"])
    
    if not col_contrato:
        return
        
    situacoes_disponiveis = sorted(df[col_contrato].dropna().astype(str).str.strip().unique().tolist())
    situacao_selecionada = st.multiselect(
        "🔎 Filtrar visualizações desta seção por situação específica:",
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
            title="Alunos por Situação do Contrato",
            color="Situação", color_discrete_sequence=CORES_PALETTE
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=380, margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with col2:
        tabela_resumo = resumo.copy()
        tabela_resumo["Percentual"] = tabela_resumo["Percentual"].map(lambda x: f"{x:.1f}%")
        st.markdown("##### 📊 Distribuição")
        st.dataframe(tabela_resumo, width="stretch", hide_index=True, height=380)

    if col_aluno and col_aluno in df_situacao.columns:
        st.markdown("#### 🔄 Situação do Contrato × Situação do Aluno")
        cruzamento_absoluto = pd.crosstab(df_situacao[col_contrato], df_situacao[col_aluno])
        cruzamento_percentual = pd.crosstab(df_situacao[col_contrato], df_situacao[col_aluno], normalize="index") * 100
        
        tab1, tab2 = st.tabs(["🔢 Valores Absolutos", "📈 Percentual por Situação (%)"])
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
        title="Distribuição de Alunos por Estado",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

# 4. FUNÇÃO PRINCIPAL
def main():
    if not renderizar_login():
        return
        
    with st.spinner("🔄 Carregando dados da planilha..."):
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
    
    st.markdown(f'<div><h1 style="display:inline; font-size: 30px; font-weight: 700; color: #1F2937;">🎓 Dashboard Acadêmico</h1> <span style="background: #F3F4F6; padding: 4px 12px; border-radius: 20px; font-size: 14px; color: #6B7280; margin-left: 12px;">{len(df_filtrado):,} registros</span></div><br>', unsafe_allow_html=True)
    
    renderizar_filtros_ativos(filtros, busca)
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum aluno encontrado com a combinação de filtros e busca selecionada. Tente ajustar os parâmetros na barra lateral.")
        return
    
    renderizar_metricas(df_filtrado)
    st.markdown("---")
    
    st.markdown("### 📈 Indicadores Acadêmicos")
    renderizar_indicadores_academicos(df_filtrado)
    st.markdown("---")
    
    st.markdown("### 🔎 Análise Detalhada de Situação")
    renderizar_analise_situacao(df_filtrado)
    st.markdown("---")
    
    st.markdown("### 📚 Análise de Cursos e Turmas")
    ca1, ca2, ca3 = st.columns(3)
    if "Curso" in df_filtrado.columns:
        ca1.plotly_chart(criar_grafico_barras(df_filtrado, "Curso", "Alunos por Curso", "h"), width="stretch")
    if "Turma" in df_filtrado.columns:
        ca2.plotly_chart(criar_grafico_barras(df_filtrado, "Turma", "Top Turmas"), width="stretch")
    col_ingresso = obter_coluna(df_filtrado, ["FormaIngresso", "Forma de Ingresso"])
    if col_ingresso:
        ca3.plotly_chart(criar_grafico_pizza(df_filtrado, col_ingresso, "Forma de Ingresso"), width="stretch")
    st.markdown("---")
    
    st.markdown("### 👤 Perfil Demográfico e Acessibilidade")
    cd1, cd2 = st.columns(2)
    if "FaixaEtaria" in df_filtrado.columns:
        cd1.plotly_chart(criar_grafico_barras(df_filtrado, "FaixaEtaria", "Distribuição por Faixa Etária"), width="stretch")
    
    col_deficiencia = obter_coluna(df_filtrado, ["Deficiência", "Deficiencia"])
    if col_deficiencia:
        cd2.plotly_chart(criar_grafico_pizza(df_filtrado, col_deficiencia, "Perfil de Acessibilidade / Deficiência"), width="stretch")
        
    cp1, cp2 = st.columns(2)
    if "Sexo" in df_filtrado.columns:
        cp1.plotly_chart(criar_grafico_pizza(df_filtrado, "Sexo", "Distribuição por Sexo"), width="stretch")
    col_raca = obter_coluna(df_filtrado, ["CorRaca", "Cor/Raça"])
    if col_raca:
        cp2.plotly_chart(criar_grafico_barras(df_filtrado, col_raca, "Cor/Raça"), width="stretch")
        
    cp3, cp4 = st.columns(2)
    if "Escolaridade" in df_filtrado.columns:
        cp3.plotly_chart(criar_grafico_barras(df_filtrado, "Escolaridade", "Escolaridade", "h"), width="stretch")
    col_prof = obter_coluna(df_filtrado, ["Profissao", "Profissão"])
    if col_prof:
        cp4.plotly_chart(criar_grafico_barras(df_filtrado, col_prof, "Top 10 Profissões", "h", top_n=10), width="stretch")
    st.markdown("---")
    
    st.markdown("### 🗺️ Distribuição Geográfica")
    if "Estado" in df_filtrado.columns and not df_filtrado["Estado"].replace("Não informado", None).dropna().empty:
        fig_mapa = criar_mapa_estados(df_filtrado)
        st.plotly_chart(fig_mapa, width="stretch")
    else:
        st.info("Nenhum dado geográfico disponível para exibir o mapa.")
    st.markdown("---")
    
    st.markdown("### 📋 Dados Completos")
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        csv = df_filtrado.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Exportar para CSV", data=csv, file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.csv", mime="text/csv", width="stretch")
        
    with btn_col2:
        with st.spinner("Preparando Excel..."):
            dados_excel = gerar_excel(df_filtrado)
        st.download_button("📊 Exportar para Excel (.xlsx)", data=dados_excel, file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        
    st.dataframe(df_filtrado, width="stretch", height=400)

if __name__ == "__main__":
    main()