import streamlit as st
import pandas as pd
import logging
import time
from datetime import datetime
from io import BytesIO

from services.google_sheets import carregar_planilha
from utils.styles import injetar_css_dark
from utils.tratamento import (
    get_column_mapping, calcular_faixa_etaria, classificar_status,
    padronizar_forma_ingresso, padronizar_cor_raca, padronizar_escolaridade, padronizar_sexo
)
from components.charts import criar_grafico_barras, criar_grafico_pizza, criar_mapa_estados
from components.views import (
    renderizar_login, renderizar_sidebar, renderizar_filtros_ativos,
    renderizar_metricas, renderizar_indicadores_academicos, renderizar_analise_situacao
)

st.set_page_config(page_title="Dashboard Acadêmico | Uníntese", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=300)
def carregar_dados() -> pd.DataFrame:
    """Pipeline de extração, limpeza seletiva e enriquecimento."""
    for i in range(2):
        try:
            df = carregar_planilha()
            mapping = get_column_mapping(df)

            colunas_texto = [c for c in df.select_dtypes(include=["object", "category"]).columns if c != mapping.get("nascimento")]
            df[colunas_texto] = df[colunas_texto].astype(str).replace(["", "nan", "None", "null", "NaN", "NAT", "<NA>"], "Não informado")
            df[colunas_texto] = df[colunas_texto].replace(r"^\s*$", "Não informado", regex=True)

            if mapping.get("ingresso"): df[mapping["ingresso"]] = df[mapping["ingresso"]].apply(padronizar_forma_ingresso)
            if mapping.get("raca"): df[mapping["raca"]] = df[mapping["raca"]].apply(padronizar_cor_raca)
            if mapping.get("escolaridade"): df[mapping["escolaridade"]] = df[mapping["escolaridade"]].apply(padronizar_escolaridade)
            if mapping.get("sexo"): df[mapping["sexo"]] = df[mapping["sexo"]].apply(padronizar_sexo)

            df = calcular_faixa_etaria(df)
            df["StatusDashboard"] = df.apply(classificar_status, axis=1)
            return df
        except Exception as e:
            if i == 1:
                st.error(f"❌ Erro de conexão com a planilha: {e}")
                return pd.DataFrame()
            time.sleep(1)

def gerar_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Alunos")
    return output.getvalue()

def main():
    if not renderizar_login(): return
    injetar_css_dark()

    with st.spinner("🔄 Carregando dados da planilha institucional..."):
        df = carregar_dados()
    if df.empty: return

    mapping = get_column_mapping(df)
    busca, filtros = renderizar_sidebar(df, mapping)
    
    df_filtrado = df.copy()
    for col, vals in filtros.items():
        if vals and col in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[col].isin(vals)]

    if busca:
        condicoes = [df_filtrado[mapping[k]].astype(str).str.contains(busca, case=False, na=False) 
                     for k in ["nome", "matricula"] if mapping.get(k) and mapping[k] in df_filtrado.columns]
        if condicoes:
            df_filtrado = df_filtrado[pd.concat(condicoes, axis=1).any(axis=1)]

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
        st.warning("⚠️ Nenhum aluno encontrado para os filtros selecionados.")
        return

    renderizar_metricas(df_filtrado)
    st.markdown("<br><div class='section-header-dark'>📈 Indicadores Acadêmicos de Retenção</div>", unsafe_allow_html=True)
    renderizar_indicadores_academicos(df_filtrado)

    st.markdown("<br><div class='section-header-dark'>🔎 Análise Detalhada de Situação Contratual</div>", unsafe_allow_html=True)
    renderizar_analise_situacao(df_filtrado, mapping)

    st.markdown("<div class='section-header-dark'>📚 Análise de Cursos, Turmas e Ingresso</div>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        tab_curso, tab_turma = st.tabs(["🎓 Top Cursos", "👥 Top Turmas"])
        with tab_curso:
            if "Curso" in df_filtrado.columns:
                st.plotly_chart(
                    criar_grafico_barras(df_filtrado, "Curso", "Top Cursos com Mais Alunos", orientation="h", top_n=8, height=380),
                    width="stretch"
                )
        with tab_turma:
            if "Turma" in df_filtrado.columns:
                st.plotly_chart(
                    criar_grafico_barras(df_filtrado, "Turma", "Top Turmas com Mais Alunos", orientation="h", top_n=8, height=380),
                    width="stretch"
                )
                
    with col_c2:
        if mapping.get("ingresso") and mapping["ingresso"] in df_filtrado.columns:
            st.plotly_chart(
                criar_grafico_pizza(df_filtrado, mapping["ingresso"], "Distribuição por Forma de Ingresso", height=415),
                width="stretch"
            )
            
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<br><div class='section-header-dark'>👤 Perfil Demográfico e Acessibilidade</div>", unsafe_allow_html=True)
    cd1, cd2 = st.columns(2)
    if "FaixaEtaria" in df_filtrado.columns: cd1.plotly_chart(criar_grafico_barras(df_filtrado, "FaixaEtaria", "Distribuição por Faixa Etária"), width="stretch")
    if mapping.get("deficiencia"): cd2.plotly_chart(criar_grafico_pizza(df_filtrado, mapping["deficiencia"], "Perfil de Acessibilidade"), width="stretch")

    cp1, cp2 = st.columns(2)
    if mapping.get("sexo"): cp1.plotly_chart(criar_grafico_pizza(df_filtrado, mapping["sexo"], "Distribuição por Sexo"), width="stretch")
    if mapping.get("raca"): cp2.plotly_chart(criar_grafico_barras(df_filtrado, mapping["raca"], "Distribuição por Cor/Raça"), width="stretch")

    cp3, cp4 = st.columns(2)
    if mapping.get("escolaridade"): cp3.plotly_chart(criar_grafico_barras(df_filtrado, mapping["escolaridade"], "Nível de Escolaridade", "h"), width="stretch")
    if mapping.get("profissao"): cp4.plotly_chart(criar_grafico_barras(df_filtrado, mapping["profissao"], "Top Profissões Declaradas", "h", top_n=10), width="stretch")

    st.markdown("<br><div class='section-header-dark'>🗺️ Distribuição Geográfica Nacional</div>", unsafe_allow_html=True)
    if "Estado" in df_filtrado.columns and not df_filtrado["Estado"].replace("Não informado", None).dropna().empty:
        st.plotly_chart(criar_mapa_estados(df_filtrado), width="stretch")

    st.markdown("<br><div class='section-header-dark'>📋 Registros Detalhados & Exportação</div>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    b1.download_button("📥 Exportar Relatório CSV", data=df_filtrado.to_csv(index=False).encode("utf-8-sig"), file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.csv", mime="text/csv", width="stretch")
    b2.download_button("📊 Exportar Relatório Excel (.xlsx)", data=gerar_excel(df_filtrado), file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    st.dataframe(df_filtrado, width="stretch", height=420)

if __name__ == "__main__":
    main()