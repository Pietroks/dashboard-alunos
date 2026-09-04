import plotly.express as px
import pandas as pd
from utils.styles import CORES_PALETTE
import plotly.graph_objects as go

def aplicar_layout_dark(fig, height: int = 380, show_legend: bool = True):
    """Padronização de layout Plotly para modo escuro."""
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

def criar_grafico_barras(df: pd.DataFrame, x: str, title: str, orientation: str = "v", top_n: int = 8, height: int = 380) -> px.bar:
    """
    Cria gráfico de barras com truncamento inteligente de nomes extensos
    e preservação do nome completo no hover (tooltip).
    """
    data = df[x].value_counts().head(top_n).reset_index()
    data.columns = [x, "Quantidade"]

    # Guarda o nome completo original para o Tooltip
    data["NomeCompleto"] = data[x].astype(str)

    # Limita o texto do eixo a 22 caracteres se for horizontal para não espremer as barras
    if orientation == "h":
        MAX_LEN = 22
        data["RotuloExibicao"] = data["NomeCompleto"].apply(
            lambda s: (s[:MAX_LEN] + "...") if len(s) > MAX_LEN else s
        )
        data = data.sort_values(by="Quantidade", ascending=True)
    else:
        MAX_LEN = 16
        data["RotuloExibicao"] = data["NomeCompleto"].apply(
            lambda s: (s[:MAX_LEN] + "...") if len(s) > MAX_LEN else s
        )

    fig = px.bar(
        data,
        x="Quantidade" if orientation == "h" else "RotuloExibicao",
        y="RotuloExibicao" if orientation == "h" else "Quantidade",
        orientation=orientation,
        title=f"<b>{title}</b>",
        color_discrete_sequence=CORES_PALETTE,
        custom_data=["NomeCompleto"],
        text="Quantidade"
    )

    # Tooltip limpo com o nome completo original
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{customdata[0]}</b><br>Quantidade: %{x if orientation == 'h' else y:,}<extra></extra>",
        marker=dict(line=dict(width=0), opacity=0.9),
        textfont=dict(color="#F1F5F9", size=11)
    )

    if orientation == "h":
        fig.update_layout(
            margin=dict(l=10, r=40, t=40, b=10),
            yaxis=dict(title=None, showgrid=False, automargin=True),
            xaxis=dict(title="Quantidade de Alunos", gridcolor="#334155")
        )
    else:
        fig.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(title=None, showgrid=False, automargin=True),
            yaxis=dict(title="Quantidade de Alunos", gridcolor="#334155")
        )

    return aplicar_layout_dark(fig, height=height, show_legend=False)

def criar_grafico_pizza(df: pd.DataFrame, names: str, title: str, height: int = 380) -> px.pie:
    """Cria gráfico donut estilizado."""
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

def criar_mapa_estados(df: pd.DataFrame) -> px.choropleth:
    """Cria mapa coroplético das UFs do Brasil."""
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

def criar_grafico_funil_retencao(df: pd.DataFrame) -> px.funnel:
    """Gera o funil acadêmico de conversão e permanência discente."""
    total = len(df)
    ativos = len(df[df["StatusDashboard"] == "ATIVO"])
    baixo_risco = len(df[(df["StatusDashboard"] == "ATIVO") & (df.get("NivelRiscoEvasao") != "Crítico")])
    # Estimativa de fluxo regular sem trancamento prévio
    regulares = len(df[(df["StatusDashboard"] == "ATIVO") & (df.get("ScoreEvasao", 0) == 0)])

    dados_funil = pd.DataFrame({
        "Etapa": [
            "1. Matrículas Registradas",
            "2. Alunos Ativos (Vigentes)",
            "3. Ativos em Situação Estável",
            "4. Fluxo Regular Pleno"
        ],
        "Discentes": [total, ativos, baixo_risco, regulares]
    })

    fig = px.funnel(
        dados_funil,
        x="Discentes",
        y="Etapa",
        title="<b>Funil de Conversão e Permanência Estudantil</b>",
        color_discrete_sequence=["#38BDF8"]
    )
    fig.update_traces(
        textinfo="value+percent initial",
        marker=dict(line=dict(width=0))
    )
    return aplicar_layout_dark(fig, height=380, show_legend=False)

def criar_grafico_cohort_temporal(df: pd.DataFrame) -> px.bar:
    """Gera a taxa de sobrevivência discente por ano de turma/ingresso."""
    if "AnoIngresso" not in df.columns:
        return None

    # Agrupa por Ano e Status
    df_tempo = df[df["AnoIngresso"].isin(["2021", "2022", "2023", "2024", "2025", "2026"])].copy()
    if df_tempo.empty:
        df_tempo = df.copy()

    crosstab = pd.crosstab(df_tempo["AnoIngresso"], df_tempo["StatusDashboard"], normalize="index") * 100
    crosstab = crosstab.reset_index().melt(id_vars="AnoIngresso", value_name="Taxa", var_name="Status")

    fig = px.bar(
        crosstab,
        x="AnoIngresso",
        y="Taxa",
        color="Status",
        title="<b>Taxa de Retenção e Sobrevivência por Ano de Turma (%)</b>",
        color_discrete_map={
            "ATIVO": "#10B981",
            "TRANCADO": "#F59E0B",
            "INATIVO": "#EF4444",
            "DESISTENTE": "#94A3B8"
        },
        barmode="stack",
        text_auto=".1f"
    )
    fig.update_layout(
        yaxis=dict(title="Percentual (%)", range=[0, 105]),
        xaxis=dict(title="Ano da Turma / Ingresso")
    )
    return aplicar_layout_dark(fig, height=380, show_legend=True)

def criar_grafico_sankey_fluxo(df: pd.DataFrame, col_ingresso: str) -> go.Figure:
    """
    Gera um diagrama de Sankey conectando:
    Forma de Ingresso -> Nível de Risco -> Status Final.
    """
    if not col_ingresso or col_ingresso not in df.columns:
        return None
    if "NivelRiscoEvasao" not in df.columns or "StatusDashboard" not in df.columns:
        return None

    # Prepara o dataframe removendo nulos nas 3 etapas
    df_fluxo = df[[col_ingresso, "NivelRiscoEvasao", "StatusDashboard"]].dropna().copy()
    if df_fluxo.empty:
        return None

    # Garante rótulos claros para evitar ambiguidades entre etapas
    df_fluxo["origem"] = df_fluxo[col_ingresso].astype(str).str.strip()
    df_fluxo["meio"] = "Risco " + df_fluxo["NivelRiscoEvasao"].astype(str).str.strip()
    df_fluxo["destino"] = "Status: " + df_fluxo["StatusDashboard"].astype(str).str.strip()

    # Identifica todos os nós únicos mantendo a ordem das etapas
    nos_origem = sorted(df_fluxo["origem"].unique().tolist())
    nos_meio = sorted(df_fluxo["meio"].unique().tolist())
    nos_destino = sorted(df_fluxo["destino"].unique().tolist())

    todos_nos = nos_origem + nos_meio + nos_destino
    mapa_indices = {nome: idx for idx, nome in enumerate(todos_nos)}

    # Etapa 1: Origem -> Meio
    fluxo_1 = df_fluxo.groupby(["origem", "meio"]).size().reset_index(name="quantidade")
    # Etapa 2: Meio -> Destino
    fluxo_2 = df_fluxo.groupby(["meio", "destino"]).size().reset_index(name="quantidade")

    sources = [mapa_indices[r["origem"]] for _, r in fluxo_1.iterrows()] + \
              [mapa_indices[r["meio"]] for _, r in fluxo_2.iterrows()]

    targets = [mapa_indices[r["meio"]] for _, r in fluxo_1.iterrows()] + \
              [mapa_indices[r["destino"]] for _, r in fluxo_2.iterrows()]

    values = fluxo_1["quantidade"].tolist() + fluxo_2["quantidade"].tolist()

    # Cores personalizadas para os nós
    cores_nos = []
    for no in todos_nos:
        if "Crítico" in no or "INATIVO" in no:
            cores_nos.append("#EF4444")      # Vermelho
        elif "Moderado" in no or "TRANCADO" in no:
            cores_nos.append("#F59E0B")      # Âmbar / Laranja
        elif "Baixo" in no or "ATIVO" in no:
            cores_nos.append("#10B981")      # Verde
        elif "DESISTENTE" in no:
            cores_nos.append("#94A3B8")      # Cinza
        else:
            cores_nos.append("#38BDF8")      # Azul padrão para ingressos

    # Configura o objeto Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=16,
            line=dict(color="#334155", width=0.5),
            label=todos_nos,
            color=cores_nos
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(148, 163, 184, 0.22)"  # Linhas semi-transparentes
        )
    )])

    fig.update_layout(
        title="<b>Fluxo Institucional: Ingresso ➔ Classificação de Risco ➔ Situação Final</b>",
        font=dict(family="Inter, sans-serif", size=11, color="#F8FAFC"),
        height=430,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig