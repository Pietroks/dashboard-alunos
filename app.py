import streamlit as st
import os
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import pandas as pd

from services.google_sheets import carregar_planilha
from utils.styles import injetar_css_dark
from utils.tratamento import (
    get_column_mapping, calcular_faixa_etaria, classificar_status,
    padronizar_forma_ingresso, padronizar_cor_raca, padronizar_escolaridade, padronizar_sexo,
    calcular_score_evasao, extrair_ano_ingresso
)
from utils.relatorios import gerar_relatorio_executivo_pdf
from components.charts import (
    criar_grafico_barras, criar_grafico_pizza, criar_mapa_estados,
    criar_grafico_funil_retencao, criar_grafico_cohort_temporal,
    criar_grafico_sankey_fluxo
)
from components.views import (
    renderizar_login, renderizar_sidebar, renderizar_filtros_ativos,
    renderizar_metricas, renderizar_indicadores_academicos, renderizar_analise_situacao,
    renderizar_painel_risco_evasao, renderizar_card_aluno_360
)
from services.query_engine import consultar_dados_duckdb

# O set_page_config deve ser a primeira chamada Streamlit do arquivo
st.set_page_config(page_title="Dashboard Acadêmico | Uníntese", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SNAPSHOT_PATH = "dados_snapshot.parquet"
FUSO_BR = ZoneInfo("America/Sao_Paulo")

def sincronizar_e_processar_dados() -> pd.DataFrame:
    """Executa o pipeline via Google Sheets com proteção contra cota 429 e fallback local."""
    max_tentativas = 3
    tempo_espera = 5

    for tentativa in range(max_tentativas):
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
            
            if "Turma" in df.columns:
                df["AnoIngresso"] = df["Turma"].apply(extrair_ano_ingresso)
            else:
                df["AnoIngresso"] = "Não informado"
                
            resultados_score = df.apply(lambda row: calcular_score_evasao(row, mapping), axis=1)
            df["ScoreEvasao"] = [r[0] for r in resultados_score]
            df["NivelRiscoEvasao"] = [r[1] for r in resultados_score]

            # Grava o snapshot Parquet
            df.to_parquet(SNAPSHOT_PATH, index=False, engine="pyarrow")
            mtime = os.path.getmtime(SNAPSHOT_PATH)
            st.session_state["ultima_sincronizacao"] = datetime.fromtimestamp(mtime, tz=FUSO_BR).strftime("%d/%m/%Y às %H:%M:%S")
            return df

        except Exception as e:
            erro_str = str(e)
            if "429" in erro_str:
                if tentativa < max_tentativas - 1:
                    time.sleep(tempo_espera * (tentativa + 1))
                    continue
            
            # Se falhar todas as tentativas, tenta recorrer ao arquivo Parquet existente
            if os.path.exists(SNAPSHOT_PATH):
                st.warning("⚠️ Limite de requisições do Google atingido temporariamente. Exibindo dados da última sincronização válida.")
                return pd.read_parquet(SNAPSHOT_PATH, engine="pyarrow")
            
            st.error(f"❌ Erro de conexão com a planilha do Google: {e}")
            return pd.DataFrame()

@st.cache_data(ttl=None)
def obter_dados(forcar_sincronizacao: bool = False) -> pd.DataFrame:
    """Retorna dados do snapshot local Parquet ou dispara o pipeline via nuvem."""
    if not forcar_sincronizacao and os.path.exists(SNAPSHOT_PATH):
        try:
            df = pd.read_parquet(SNAPSHOT_PATH, engine="pyarrow")
            if "ultima_sincronizacao" not in st.session_state:
                mtime = os.path.getmtime(SNAPSHOT_PATH)
                st.session_state["ultima_sincronizacao"] = datetime.fromtimestamp(mtime, tz=FUSO_BR).strftime("%d/%m/%Y às %H:%M:%S")
            return df
        except Exception as e:
            logger.warning(f"Falha ao ler snapshot parquet ({e}), reprocessando via API...")

    return sincronizar_e_processar_dados()

def gerar_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Alunos")
    return output.getvalue()

def main():
    if not renderizar_login(): return
    injetar_css_dark()

    with st.spinner("⚡ Carregando base otimizada..."):
        df = obter_dados(forcar_sincronizacao=st.session_state.get("disparar_sincronizacao", False))
        if st.session_state.get("disparar_sincronizacao"):
            st.session_state["disparar_sincronizacao"] = False

    if df.empty: return

    mapping = get_column_mapping(df)
    busca, filtros = renderizar_sidebar(df, mapping)
    
    if os.path.exists(SNAPSHOT_PATH):
        df_filtrado = consultar_dados_duckdb(
            parquet_path=SNAPSHOT_PATH,
            filtros=filtros,
            busca=busca,
            mapping=mapping
        )
    else:
        # Fallback de segurança para memória
        df_filtrado = df.copy()
        for col, vals in filtros.items():
            if vals and col in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[col].isin(vals)]
        if busca:
            mascara = pd.Series(False, index=df_filtrado.index)
            for k in ["nome", "matricula"]:
                col = mapping.get(k)
                if col and col in df_filtrado.columns:
                    mascara |= df_filtrado[col].astype(str).str.contains(busca, case=False, na=False)
            df_filtrado = df_filtrado[mascara]

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
        
    col_nome = mapping.get("nome", "Nome")
    col_matr = mapping.get("matricula", "Matrícula")

    aluno_escolhido = None

    if len(df_filtrado) == 1:
        aluno_escolhido = df_filtrado.iloc[0]
    else:
        with st.expander("👤 Consultar Ficha Cadastral de um Aluno Específico", expanded=False):
            def limpar_busca_ficha():
                st.session_state["termo_ficha"] = ""

            c_busca, c_limpar = st.columns([0.88, 0.12])
            with c_busca:
                termo_ficha = st.text_input(
                    "Digite o Nome ou Matrícula do aluno:",
                    placeholder="Ex: Jão ou 17346...",
                    key="termo_ficha"
                ).strip()
            with c_limpar:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.session_state.get("termo_ficha"):
                    st.button("Limpar", on_click=limpar_busca_ficha, key="btn_limpar_ficha", width="stretch")

            if termo_ficha:
                cond_nome = df_filtrado[col_nome].astype(str).str.contains(termo_ficha, case=False, na=False) if col_nome else False
                cond_matr = df_filtrado[col_matr].astype(str).str.contains(termo_ficha, case=False, na=False) if col_matr else False
                candidatos = df_filtrado[cond_nome | cond_matr]

                if candidatos.empty:
                    st.info(f"Nenhum discente encontrado com o termo '{termo_ficha}'.")
                elif len(candidatos) == 1:
                    aluno_escolhido = candidatos.iloc[0]
                else:
                    st.markdown(f"**Encontrados {len(candidatos)} discentes:** selecione um abaixo:")
                    opcoes = {
                        f"👤 {row[col_nome]} | Matrícula: {row[col_matr]} ({row.get('Curso', 'Curso')})": row
                        for _, row in candidatos.head(10).iterrows()
                    }
                    escolhido_label = st.radio("Selecione o discente:", list(opcoes.keys()), label_visibility="collapsed")
                    if escolhido_label:
                        aluno_escolhido = opcoes[escolhido_label]

    if aluno_escolhido is not None:
        renderizar_card_aluno_360(aluno_escolhido, mapping)

    renderizar_metricas(df_filtrado, mapping)
    st.markdown("<br><div class='section-header-dark'>📈 Indicadores Acadêmicos de Retenção</div>", unsafe_allow_html=True)
    renderizar_indicadores_academicos(df_filtrado)
    
    st.markdown("<div class='section-header-dark'>⏳ Evolução Temporal & Funil de Conversão</div>", unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fig_funil = criar_grafico_funil_retencao(df_filtrado)
        st.plotly_chart(fig_funil, width="stretch")
    with col_t2:
        fig_cohort = criar_grafico_cohort_temporal(df_filtrado)
        if fig_cohort:
            st.plotly_chart(fig_cohort, width="stretch")
        else:
            st.info("Dados insuficientes de turmas com ano definido para o gráfico temporal.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    renderizar_painel_risco_evasao(df_filtrado, mapping)

    col_ingresso = mapping.get("ingresso")
    if col_ingresso and col_ingresso in df_filtrado.columns:
        st.markdown("<br><div class='section-header-dark'>🌊 Matriz de Transição e Churn Discente</div>", unsafe_allow_html=True)
        fig_sankey = criar_grafico_sankey_fluxo(df_filtrado, col_ingresso)
        if fig_sankey:
            st.plotly_chart(fig_sankey, width="stretch")
        else:
            st.info("Dados insuficientes para gerar a matriz de fluxo discente.")
    # -------------------------------------------------------------------------

    st.markdown("<br><div class='section-header-dark'>🔎 Análise Detalhada de Situação Contratual</div>", unsafe_allow_html=True)
    renderizar_analise_situacao(df_filtrado, mapping)

    st.markdown("<div class='section-header-dark'>📚 Análise de Cursos, Turmas e Desempenho Acadêmico</div>", unsafe_allow_html=True)
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
        col_ingresso = mapping.get("ingresso")
        col_aluno = mapping.get("aluno")
        
        # Cria abas para Ingresso e Situação Pedagógica
        tab_pedag, tab_ingr = st.tabs(["🎯 Situação Acadêmica (Aprovações)", "🚪 Forma de Ingresso"])
        
        with tab_pedag:
            if col_aluno and col_aluno in df_filtrado.columns:
                st.plotly_chart(
                    criar_grafico_pizza(df_filtrado, col_aluno, "Distribuição por Situação Acadêmica", height=380),
                    width="stretch"
                )
            else:
                st.info("Dado de situação acadêmica não disponível.")

        with tab_ingr:
            if col_ingresso and col_ingresso in df_filtrado.columns:
                st.plotly_chart(
                    criar_grafico_pizza(df_filtrado, col_ingresso, "Distribuição por Forma de Ingresso", height=380),
                    width="stretch"
                )
            
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<div class='section-header-dark'>👤 Perfil Demográfico e Acessibilidade</div>", unsafe_allow_html=True)
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
    b1, b2, b3 = st.columns(3)
    b1.download_button("📥 Exportar Relatório CSV", data=df_filtrado.to_csv(index=False).encode("utf-8-sig"), file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.csv", mime="text/csv", width="stretch")
    b2.download_button("📊 Exportar Relatório Excel (.xlsx)", data=gerar_excel(df_filtrado), file_name=f"dashboard_{datetime.now():%Y%m%d_%H%M%S}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    with b3:
        pdf_executivo = gerar_relatorio_executivo_pdf(df_filtrado, mapping)
        st.download_button(
            "📑 Baixar Relatório Executivo (PDF)",
            data=pdf_executivo,
            file_name=f"relatorio_executivo_unintese_{datetime.now():%Y%m%d_%H%M}.pdf",
            mime="application/pdf",
            type="primary",
            width="stretch"
        )

    st.dataframe(
        df_filtrado,
        column_config={
            "ScoreEvasao": st.column_config.ProgressColumn(
                "Score de Risco",
                help="Pontuação calculada de propensão à evasão",
                format="%d pts",
                min_value=0,
                max_value=100,
            ),
            "StatusDashboard": st.column_config.TextColumn(
                "Status Executivo",
                help="Vínculo institucional consolidado"
            ),
        },
        width="stretch",
        height=450,
        hide_index=True
    )

if __name__ == "__main__":
    main()