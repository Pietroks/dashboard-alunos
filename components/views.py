import streamlit as st
import pandas as pd
import hashlib
import plotly.express as px
from typing import Dict, List, Any, Tuple
from services.auth import inicializar_banco, verificar_credenciais
from utils.styles import injetar_css_dark, CORES_STATUS, CORES_PALETTE, METRICAS_CONFIG
from components.charts import aplicar_layout_dark
from utils.relatorios import gerar_ficha_aluno_pdf

# Chave secreta interna para assinar o token de sessão local
SECRET_SALT = "unintese_dashboard_secret_key_2026"

def gerar_token_sessao(usuario: str, nome: str) -> str:
    """Gera um hash simples baseado no usuário para validação na URL."""
    return hashlib.sha256(f"{usuario}:{nome}:{SECRET_SALT}".encode()).hexdigest()[:24]

def renderizar_login() -> bool:
    """Gerencia a autenticação persistente via st.session_state e st.query_params."""
    inicializar_banco()

    params = st.query_params
    user_param = params.get("user")
    name_param = params.get("name")
    token_param = params.get("token")

    if user_param and name_param and token_param:
        token_esperado = gerar_token_sessao(user_param, name_param)
        if token_param == token_esperado:
            st.session_state["autenticado"] = True
            st.session_state["usuario_nome"] = name_param
            st.session_state["usuario_login"] = user_param

    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["usuario_nome"] = ""

    if not st.session_state["autenticado"]:
        injetar_css_dark()
        _, col2, _ = st.columns([1, 1.2, 1])
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
                usuario = st.text_input("Usuário", placeholder="ex: admin").strip().lower()
                senha = st.text_input("Senha", type="password", placeholder="••••••••")
                btn_entrar = st.form_submit_button("Entrar no Painel", width="stretch", type="primary")

                if btn_entrar:
                    nome = verificar_credenciais(usuario, senha)
                    if nome:
                        token = gerar_token_sessao(usuario, nome)
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_nome"] = nome
                        st.session_state["usuario_login"] = usuario
                        st.query_params["user"] = usuario
                        st.query_params["name"] = nome
                        st.query_params["token"] = token
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")
        return False
    return True

def resetar_filtros():
    """Limpa filtros e busca na sessão."""
    for k in list(st.session_state.keys()):
        if k.startswith("f_"):
            st.session_state[k] = []
        elif k == "busca_input":
            st.session_state["busca_input"] = ""

def renderizar_sidebar(df: pd.DataFrame, mapping: Dict[str, Any]) -> Tuple[str, Dict[str, List[Any]]]:
    """Renderiza os seletores da barra lateral e busca textual."""
    filtros = {}
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
            st.query_params.clear() 
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
        if mapping.get("contrato"):
            colunas_candidatas.append(("Situação do Contrato", mapping["contrato"]))
        if mapping.get("deficiencia"):
            colunas_candidatas.append(("Deficiência", mapping["deficiencia"]))

        for label, coluna in colunas_candidatas:
            if coluna in df.columns:
                opcoes = sorted([str(x) for x in df[coluna].unique() if str(x) != "nan"])
                filtros[coluna] = st.multiselect(label, opcoes, placeholder="Todos", key=f"f_{coluna}")

        st.markdown("---")
        st.button("🔄 Limpar Filtros", on_click=resetar_filtros, width="stretch")

        # Exibe status e timestamp da última sincronização
        ts_sinc = st.session_state.get("ultima_sincronizacao", "Não registrada")
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #334155; padding: 10px; border-radius: 8px; margin-top: 12px; margin-bottom: 8px;">
            <div style="font-size: 10px; color: #64748B; font-weight: 600; text-transform: uppercase;">Última Sincronização</div>
            <div style="font-size: 12px; color: #38BDF8; font-weight: 500; margin-top: 2px;">🕒 {ts_sinc}</div>
        </div>
        """, unsafe_allow_html=True)

        def disparar_sync():
            st.session_state["disparar_sincronizacao"] = True
            st.cache_data.clear()

        st.button("⚡ Sincronizar Planilha em Nuvem", on_click=disparar_sync, width="stretch", type="secondary")

    return busca, filtros

def renderizar_filtros_ativos(filtros: Dict[str, List[Any]], busca: str):
    filtros_selecionados = [f"<b>{col}</b>: {', '.join(map(str, vals))}" for col, vals in filtros.items() if vals]
    if busca:
        filtros_selecionados.insert(0, f"<b>Busca</b>: '{busca}'")

    if filtros_selecionados:
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38BDF8; padding: 10px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 20px;">
            📌 <b>Filtros Ativos:</b> {' &nbsp;|&nbsp; '.join(filtros_selecionados)}
        </div>
        """, unsafe_allow_html=True)

def renderizar_metricas(df: pd.DataFrame):
    counts = df["StatusDashboard"].value_counts().to_dict() if "StatusDashboard" in df.columns else {}
    metricas = {
        "total": len(df),
        "ATIVO": counts.get("ATIVO", 0),
        "FORMADO": counts.get("FORMADO", 0),
        "TRANCADO": counts.get("TRANCADO", 0),
        "INATIVO": counts.get("INATIVO", 0),
        "DESISTENTE": counts.get("DESISTENTE", 0),
    }

    cols = st.columns(len(METRICAS_CONFIG))
    for i, config in enumerate(METRICAS_CONFIG):
        with cols[i]:
            cor, bg = config["color"], config["bg"]
            st.markdown(f"""
            <div class="metric-card-dark" style="border-top: 3px solid {cor};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; font-weight: 600; color: #94A3B8;">{config['label']}</span>
                    <span style="background: {bg}; color: {cor}; padding: 4px 8px; border-radius: 8px; font-size: 14px;">{config['icon']}</span>
                </div>
                <div style="font-size: 26px; font-weight: 700; color: #F8FAFC; margin-top: 10px;">
                    {metricas[config['key']]:,}
                </div>
            </div>
            """, unsafe_allow_html=True)

def renderizar_indicadores_academicos(df: pd.DataFrame):
    total = len(df)
    counts = df["StatusDashboard"].value_counts().to_dict() if "StatusDashboard" in df.columns else {}
    status_ordem = ["ATIVO", "FORMADO", "TRANCADO", "INATIVO", "DESISTENTE"]
    
    indicadores = {s: counts.get(s, 0) for s in status_ordem}
    percentuais = {s: (qtd / total * 100) if total > 0 else 0 for s, qtd in indicadores.items()}

    cols = st.columns(len(status_ordem))
    for i, status in enumerate(status_ordem):
        with cols[i]:
            cor, qtd, pct = CORES_STATUS[status], indicadores[status], percentuais[status]
            st.markdown(f"""
            <div class="metric-card-dark" style="border-left: 4px solid {cor};">
                <div style="font-size: 12px; font-weight: 600; color: #94A3B8; text-transform: uppercase;">{status}</div>
                <div style="font-size: 24px; font-weight: 700; color: {cor}; margin-top: 4px;">{pct:.1f}%</div>
                <div style="font-size: 13px; color: #64748B; margin-top: 2px;">{qtd:,} estudantes</div>
            </div>
            """, unsafe_allow_html=True)

def renderizar_analise_situacao(df: pd.DataFrame, mapping: Dict[str, Any]):
    col_contrato = mapping.get("contrato")
    col_aluno = mapping.get("aluno")
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

def renderizar_painel_risco_evasao(df: pd.DataFrame, mapping: Dict[str, Any]):
    df_ativos = df[df["StatusDashboard"] == "ATIVO"].copy()
    if df_ativos.empty:
        return

    criticos = df_ativos[df_ativos["NivelRiscoEvasao"] == "Crítico"]
    moderados = df_ativos[df_ativos["NivelRiscoEvasao"] == "Moderado"]
    baixos = df_ativos[df_ativos["NivelRiscoEvasao"] == "Baixo"]
    
    col_titulo, col_info = st.columns([0.96, 0.04])
    with col_titulo:
        st.markdown("<div class='section-header-dark' style='margin-top: 0;'>🎯 Análise Preditiva de Risco de Evasão (Alunos Ativos)</div>", unsafe_allow_html=True)
    with col_info:
        with st.popover("❔", help="Clique para entender a metodologia do Score"):
            st.markdown("""
            **Metodologia de Triagem de Evasão**
            
            O score (0 a 100) quantifica a vulnerabilidade com base no histórico da instituição:
            - **+30 pts:** Demanda de acessibilidade (PcD)
            - **+25 pts:** Ingresso por Transferência ou Reingresso
            - **+25 pts:** Pendência Contratual/Documental
            - **+20 pts:** Faixa etária acima de 35 anos
            
            ---
            - 🔴 **Crítico (≥ 60 pts):** Intervenção imediata da tutoria.
            - 🟡 **Moderado (35 a 59 pts):** Acompanhamento preventivo.
            - 🟢 **Baixo (< 35 pts):** Fluxo regular.
            """)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""
    <div class="metric-card-dark" style="border-left: 4px solid #EF4444;">
        <div style="font-size: 12px; font-weight: 600; color: #94A3B8;">🔴 RISCO CRÍTICO</div>
        <div style="font-size: 24px; font-weight: 700; color: #EF4444; margin-top: 4px;">{len(criticos):,} discentes</div>
        <div style="font-size: 12px; color: #64748B;">Requer intervenção imediata</div>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="metric-card-dark" style="border-left: 4px solid #F59E0B;">
        <div style="font-size: 12px; font-weight: 600; color: #94A3B8;">🟡 RISCO MODERADO</div>
        <div style="font-size: 24px; font-weight: 700; color: #F59E0B; margin-top: 4px;">{len(moderados):,} discentes</div>
        <div style="font-size: 12px; color: #64748B;">Acompanhamento preventivo</div>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="metric-card-dark" style="border-left: 4px solid #10B981;">
        <div style="font-size: 12px; font-weight: 600; color: #94A3B8;">🟢 RISCO BAIXO</div>
        <div style="font-size: 24px; font-weight: 700; color: #10B981; margin-top: 4px;">{len(baixos):,} discentes</div>
        <div style="font-size: 12px; color: #64748B;">Fluxo acadêmico regular</div>
    </div>
    """, unsafe_allow_html=True)

    if not criticos.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🚨 Ver Lista de Atendimento Prioritário da Tutoria (Risco Crítico)", expanded=False):
            col_nome = mapping.get("nome", "Nome")
            col_matr = mapping.get("matricula", "Matrícula")
            col_curso = "Curso" if "Curso" in criticos.columns else None

            cols_exibicao = [c for c in [col_matr, col_nome, col_curso, "ScoreEvasao", "FaixaEtaria"] if c and c in criticos.columns]
            
            st.dataframe(
                criticos[cols_exibicao].sort_values(by="ScoreEvasao", ascending=False),
                width="stretch",
                hide_index=True
            )

def renderizar_card_aluno_360(aluno: pd.Series, mapping: Dict[str, Any]):
    nome = aluno.get(mapping.get("nome", "Nome"), "Não informado")
    matricula = aluno.get(mapping.get("matricula", "Matrícula"), "Não informado")
    curso = aluno.get("Curso", "Não informado")
    turma = aluno.get("Turma", "Não informado")
    status = str(aluno.get("StatusDashboard", "ATIVO")).upper()
    contrato = aluno.get(mapping.get("contrato", ""), "Não informado")
    ingresso = aluno.get(mapping.get("ingresso", ""), "Não informado")
    faixa = aluno.get("FaixaEtaria", "Não informado")
    score = aluno.get("ScoreEvasao", 0)
    nivel_risco = aluno.get("NivelRiscoEvasao", "Baixo")
    uf = aluno.get("Estado", "Não informado")
    cidade = aluno.get("Cidade", "Não informado")
    pcd = aluno.get(mapping.get("deficiencia", ""), "Não informado")

    cor_status = CORES_STATUS.get(status, "#38BDF8")
    cor_risco = "#EF4444" if nivel_risco == "Crítico" else ("#F59E0B" if nivel_risco == "Moderado" else "#10B981")

    st.markdown(f"""
    <div style="background: #1E293B; border-radius: 14px; border: 1px solid #334155; padding: 20px; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 16px;">
            <div>
                <span style="font-size: 11px; font-weight: 700; color: #38BDF8; text-transform: uppercase; letter-spacing: 0.05em;">Ficha Cadastral 360° do Discente</span>
                <h2 style="font-size: 22px; font-weight: 800; color: #F8FAFC; margin: 2px 0 0 0;">👤 {nome}</h2>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(56, 189, 248, 0.1); color: {cor_status}; border: 1px solid {cor_status}; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px;">{status}</span>
                <div style="color: #94A3B8; font-size: 12px; margin-top: 4px;">Matrícula: <b>{matricula}</b></div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">CURSO</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{curso}</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">TURMA</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{turma}</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">SITUAÇÃO CONTRATUAL</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{contrato}</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">FORMA DE INGRESSO</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{ingresso}</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">SCORE DE EVASÃO</div>
                <div style="color: {cor_risco}; font-size: 13px; font-weight: 700; margin-top: 2px;">{score} pts ({nivel_risco})</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">FAIXA ETÁRIA</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{faixa}</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">POLO / LOCALIZAÇÃO</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{cidade} - {uf}</div>
            </div>
            <div>
                <div style="color: #64748B; font-size: 11px; font-weight: 600;">ACESSIBILIDADE / PCD</div>
                <div style="color: #F1F5F9; font-size: 13px; font-weight: 600; margin-top: 2px;">{pcd}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pdf_bytes = gerar_ficha_aluno_pdf(aluno, mapping)
    st.download_button(
        label=f"📄 Baixar Ficha Cadastral Oficial (PDF) - {matricula}",
        data=pdf_bytes,
        file_name=f"ficha_academica_{matricula}.pdf",
        mime="application/pdf",
        type="primary"
    )
    st.markdown("<br>", unsafe_allow_html=True)