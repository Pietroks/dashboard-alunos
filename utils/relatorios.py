from io import BytesIO
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def gerar_ficha_aluno_pdf(aluno: pd.Series, mapping: dict) -> bytes:
    """Gera um PDF formal com a ficha cadastral 360° do discente."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    # Estilos de tipografia institucional
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
        spaceAfter=16
    )

    story.append(Paragraph("FACULDADE UNÍNTESE • GESTÃO ACADÊMICA", title_style))
    story.append(Paragraph("FICHA CADASTRAL INDIVIDUAL DO DISCENTE (VISÃO 360°)", sub_style))

    # Extração segura de campos
    nome = str(aluno.get(mapping.get("nome", "Nome"), "Não informado"))
    matricula = str(aluno.get(mapping.get("matricula", "Matrícula"), "Não informado"))
    curso = str(aluno.get("Curso", "Não informado"))
    turma = str(aluno.get("Turma", "Não informado"))
    status = str(aluno.get("StatusDashboard", "Não informado"))
    contrato = str(aluno.get(mapping.get("contrato", ""), "Não informado"))
    ingresso = str(aluno.get(mapping.get("ingresso", ""), "Não informado"))
    faixa_etaria = str(aluno.get("FaixaEtaria", "Não informado"))
    nasc = str(aluno.get(mapping.get("nascimento", ""), "Não informado"))
    sexo = str(aluno.get(mapping.get("sexo", "Sexo"), "Não informado"))
    raca = str(aluno.get(mapping.get("raca", ""), "Não informado"))
    defic = str(aluno.get(mapping.get("deficiencia", ""), "Não informado"))
    escolaridade = str(aluno.get(mapping.get("escolaridade", "Escolaridade"), "Não informado"))
    cidade = str(aluno.get("Cidade", "Não informado"))
    estado = str(aluno.get("Estado", "Não informado"))
    score = f"{aluno.get('ScoreEvasao', 0)} pts ({aluno.get('NivelRiscoEvasao', 'Baixo')})"

    tabela_dados = [
        ["Nome do Discente:", nome, "Matrícula:", matricula],
        ["Curso:", curso, "Turma:", turma],
        ["Status Acadêmico:", status, "Situação Contratual:", contrato],
        ["Forma de Ingresso:", ingresso, "Score de Evasão:", score],
        ["Data de Nascimento:", nasc, "Faixa Etária:", faixa_etaria],
        ["Sexo:", sexo, "Cor / Raça:", raca],
        ["Acessibilidade / PcD:", defic, "Escolaridade Prévia:", escolaridade],
        ["Município / UF:", f"{cidade} - {estado}", "Data de Emissão:", datetime.now().strftime("%d/%m/%Y %H:%M")]
    ]

    t = Table(tabela_dados, colWidths=[130, 140, 130, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#0F172A")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    obs_style = ParagraphStyle(
        "ObsStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.HexColor("#94A3B8"),
        alignment=0
    )
    story.append(Paragraph("Documento emitido eletronicamente para fins de acompanhamento psicopedagógico e auditoria acadêmica interna. Protegido nos termos da LGPD.", obs_style))

    doc.build(story)
    return buffer.getvalue()

def gerar_relatorio_executivo_pdf(df: pd.DataFrame, mapping: dict) -> bytes:
    """Gera um PDF formal consolidado para reuniões de colegiado e diretoria."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ExecTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16, textColor=colors.HexColor("#0F172A"), alignment=1, spaceAfter=2
    )
    sub_style = ParagraphStyle(
        "ExecSub", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#64748B"), alignment=1, spaceAfter=12
    )
    h2_style = ParagraphStyle(
        "ExecH2", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#1E293B"), spaceBefore=10, spaceAfter=6
    )
    body_style = ParagraphStyle(
        "ExecBody", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#334155"), leading=11
    )

    story.append(Paragraph("FACULDADE UNÍNTESE • DIRETORIA & COORDENAÇÃO ACADÊMICA", title_style))
    story.append(Paragraph(f"RELATÓRIO EXECUTIVO DE GESTÃO DA PERMANÊNCIA E RETENÇÃO • EMISSÃO: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=12))

    total = len(df)
    counts = df["StatusDashboard"].value_counts().to_dict() if "StatusDashboard" in df.columns else {}
    ativos = counts.get("ATIVO", 0)
    inativos = counts.get("INATIVO", 0)
    desistentes = counts.get("DESISTENTE", 0)
    trancados = counts.get("TRANCADO", 0)

    # 1. Tabela de Indicadores Gerais
    story.append(Paragraph("<b>1. RESUMO EXECUTIVO DE MATRÍCULAS E RETENÇÃO</b>", h2_style))
    kpi_data = [
        ["TOTAL ANALISADO", "ALUNOS ATIVOS", "INATIVOS", "DESISTENTES", "TRANCADOS"],
        [
            f"{total:,}",
            f"{ativos:,} ({(ativos/total*100):.1f}%)" if total else "0",
            f"{inativos:,} ({(inativos/total*100):.1f}%)" if total else "0",
            f"{desistentes:,} ({(desistentes/total*100):.1f}%)" if total else "0",
            f"{trancados:,} ({(trancados/total*100):.1f}%)" if total else "0",
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[105, 105, 105, 105, 105])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 7.5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor("#0F172A")),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # 2. Diagnóstico de Risco Preditivo de Evasão (Alunos Ativos)
    story.append(Paragraph("<b>2. DIAGNÓSTICO PREDITIVO DE EVASÃO (ALUNOS ATIVOS)</b>", h2_style))
    df_ativos = df[df["StatusDashboard"] == "ATIVO"]
    criticos = len(df_ativos[df_ativos["NivelRiscoEvasao"] == "Crítico"]) if "NivelRiscoEvasao" in df_ativos.columns else 0
    moderados = len(df_ativos[df_ativos["NivelRiscoEvasao"] == "Moderado"]) if "NivelRiscoEvasao" in df_ativos.columns else 0
    baixos = len(df_ativos[df_ativos["NivelRiscoEvasao"] == "Baixo"]) if "NivelRiscoEvasao" in df_ativos.columns else 0

    risco_data = [
        ["Classificação de Risco", "Quantidade", "Percentual s/ Ativos", "Ação Recomendada"],
        ["Risco Crítico (Score >= 60)", f"{criticos:,}", f"{(criticos/ativos*100):.1f}%" if ativos else "0%", "Intervenção e busca ativa imediata da tutoria"],
        ["Risco Moderado (Score 35-59)", f"{moderados:,}", f"{(moderados/ativos*100):.1f}%" if ativos else "0%", "Acompanhamento acadêmico preventivo"],
        ["Risco Baixo (Score < 35)", f"{baixos:,}", f"{(baixos/ativos*100):.1f}%" if ativos else "0%", "Fluxo acadêmico regular mantido"]
    ]
    t_risco = Table(risco_data, colWidths=[150, 75, 100, 200])
    t_risco.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 7.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_risco)
    story.append(Spacer(1, 10))

    # 3. Top Cursos
    if "Curso" in df.columns:
        story.append(Paragraph("<b>3. DISTRIBUIÇÃO DOS PRINCIPAIS CURSOS</b>", h2_style))
        top_cursos = df["Curso"].value_counts().head(6).reset_index()
        top_cursos.columns = ["Curso", "Discentes"]
        top_cursos["Percentual"] = (top_cursos["Discentes"] / total * 100).map(lambda x: f"{x:.1f}%")
        
        curso_rows = [["Curso Acadêmico", "Total Discentes", "Representatividade (%)"]]
        for _, r in top_cursos.iterrows():
            curso_rows.append([str(r["Curso"])[:50], f"{r['Discentes']:,}", r["Percentual"]])

        t_curso = Table(curso_rows, colWidths=[330, 100, 95])
        t_curso.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 7.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_curso)

    story.append(Spacer(1, 16))
    story.append(Paragraph("<i>Relatório institucional para uso exclusivo da Diretoria e Coordenações da Faculdade Uníntese. Documento protegido pela LGPD.</i>", body_style))

    doc.build(story)
    return buffer.getvalue()