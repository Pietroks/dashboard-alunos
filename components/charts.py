import plotly.express as px
import pandas as pd
from utils.styles import CORES_PALETTE

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