import unicodedata
import pandas as pd
from typing import Optional, List, Dict
import re

def extrair_ano_ingresso(turma: str) -> str:
    """Extrai o ano da turma para análise temporal de cohorts."""
    if not turma or str(turma).strip() in ["", "Não informado", "nan", "None", "<NA>"]:
        return "Não informado"
    s = str(turma).strip()
    
    # 1. 4 dígitos começando com 20 (ex: 2021 a 2029)
    m4 = re.search(r'\b(20[12][0-9])\b', s)
    if m4:
        return m4.group(1)
        
    # 2. Padrão de código institucional (ex: 1024 -> ano 2024, 2023 -> 2023)
    m_cod = re.search(r'([0-9]{2})(2[0-9])\b', s)
    if m_cod:
        return f"20{m_cod.group(2)}"
        
    # 3. Padrão com separador (ex: ADS-23, PED/24, TURMA_22)
    m2 = re.search(r'[_\-\/\.](2[0-9])\b', s)
    if m2:
        return f"20{m2.group(1)}"
        
    return "Outros"

def remover_acentos(texto: str) -> str:
    """Remove acentos e caracteres diacríticos para comparação insensível."""
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')

def obter_coluna(df: pd.DataFrame, opcoes: List[str]) -> Optional[str]:
    """Retorna a primeira coluna existente correspondente em O(1)."""
    colunas_set = set(df.columns)
    for col in opcoes:
        if col in colunas_set:
            return col
    return None

def get_column_mapping(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Mapeamento direto de colunas sem sobrecarga de hash."""
    return {
        "nascimento": obter_coluna(df, ["DataNascimento", "Data Nascimento", "Nascimento"]),
        "contrato": obter_coluna(df, ["Situacao do contrato", "Situação do contrato"]),
        "aluno": obter_coluna(df, ["Situacao do aluno", "Situação do aluno"]),
        "deficiencia": obter_coluna(df, ["Deficiência", "Deficiencia"]),
        "ingresso": obter_coluna(df, ["FormaIngresso", "Forma de Ingresso"]),
        "profissao": obter_coluna(df, ["Profissao", "Profissão"]),
        "raca": obter_coluna(df, ["CorRaca", "Cor/Raça"]),
        "nome": obter_coluna(df, ["Nome", "Aluno"]),
        "matricula": obter_coluna(df, ["Matricula", "Matrícula"]),
        "escolaridade": obter_coluna(df, ["Escolaridade", "Grau de Escolaridade", "GrauInstrucao"]),
        "sexo": obter_coluna(df, ["Sexo", "Gênero", "Genero"]),
    }

def padronizar_forma_ingresso(val: str) -> str:
    """Padroniza variações da forma de ingresso."""
    if not val:
        return "Não informado"
    s = remover_acentos(str(val)).strip().upper()
    if s in ["", "NAN", "NONE", "NULL", "NAO INFORMADO", "NAO DECLARADO", "<NA>", "NAT"]:
        return "Não informado"

    if "ENEM" in s:
        return "ENEM"
    elif "VESTIBULAR" in s:
        return "Vestibular"
    elif "TRANSFER" in s:
        return "Transferência"
    elif any(k in s for k in ["DIPLOMA", "GRADUACAO", "SEGUNDA", "2A", "SUPERIOR"]):
        return "Segunda Graduação / Portador de Diploma"
    elif any(k in s for k in ["REABERTURA", "REINGRESSO"]):
        return "Reingresso / Reabertura"
    
    return str(val).strip().title()

def padronizar_cor_raca(val: str) -> str:
    """Padroniza variações de cor/raça (padrão IBGE)."""
    if not val:
        return "Não informado"
    s = remover_acentos(str(val)).strip().upper()
    if s in ["", "NAN", "NONE", "NULL", "NAO INFORMADO", "NAO DECLARADO", "RECUSA EM DECLARAR", "<NA>", "NAT"]:
        return "Não informado"

    if "BRANC" in s:
        return "Branca"
    elif "PARD" in s:
        return "Parda"
    elif "PRET" in s or "NEGR" in s:
        return "Preta"
    elif "AMAREL" in s:
        return "Amarela"
    elif "INDIG" in s:
        return "Indígena"
    
    return str(val).strip().title()

def padronizar_escolaridade(val: str) -> str:
    """Padroniza variações e níveis de escolaridade."""
    if not val:
        return "Não informado"
    s = remover_acentos(str(val)).strip().upper()
    if s in ["", "NAN", "NONE", "NULL", "NAO INFORMADO", "NAO DECLARADO", "<NA>", "NAT"]:
        return "Não informado"

    if "DOUTOR" in s:
        return "Pós-Graduação (Doutorado)"
    elif "MESTRADO" in s:
        return "Pós-Graduação (Mestrado)"
    elif "POS-GRADUA" in s or "POS GRADUA" in s or "LATO" in s or "LATU" in s or "ESPECIALIZA" in s:
        if "INCOMPLETO" in s:
            return "Pós-Graduação - Incompleto"
        return "Pós-Graduação (Lato Sensu) - Completo"
    elif "SUPERIOR" in s or "GRADUA" in s:
        if "INCOMPLETO" in s:
            return "Superior - Incompleto"
        return "Superior - Completo"
    elif "MEDIO" in s or "2 GRAU" in s or "SEGUNDO GRAU" in s:
        if "INCOMPLETO" in s:
            return "Médio - Incompleto"
        return "Médio - Completo"
    elif "FUNDAMENTAL" in s or "1 GRAU" in s or "PRIMEIRO GRAU" in s:
        if "INCOMPLETO" in s:
            return "Fundamental - Incompleto"
        return "Fundamental - Completo"

    return str(val).strip().title()

def padronizar_sexo(val: str) -> str:
    """Padroniza Masculino/Feminino."""
    if not val:
        return "Não informado"
    s = str(val).strip().upper()
    if s in ["M", "MASC", "MASCULINO"]:
        return "Masculino"
    elif s in ["F", "FEM", "FEMININO"]:
        return "Feminino"
    return "Não informado"

def calcular_faixa_etaria(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a faixa etária tratando números seriais do Excel e datas textuais."""
    col_nasc = obter_coluna(df, ["DataNascimento", "Data Nascimento", "Nascimento"])
    if not col_nasc or col_nasc not in df.columns:
        df["FaixaEtaria"] = "Não informado"
        return df

    serie = df[col_nasc]
    serie_num = pd.to_numeric(serie, errors="coerce")
    serie_valida = serie_num.where((serie_num >= 1) & (serie_num <= 50000))
    datas_num = pd.to_datetime(serie_valida, unit="D", origin="1899-12-30", errors="coerce")
    
    datas_str = pd.to_datetime(serie.astype(str).replace(["Não informado", "nan", "None", "<NA>"], None), errors="coerce", dayfirst=True)
    nascimento_dt = datas_num.combine_first(datas_str)

    df[col_nasc] = nascimento_dt.dt.strftime("%d/%m/%Y").fillna("Não informado")

    hoje = pd.Timestamp.now()
    idades = (hoje - nascimento_dt).dt.days // 365.25

    bins = [0, 17, 24, 34, 44, 54, 120]
    labels = ["Menor de 18", "18–24 anos", "25–34 anos", "35–44 anos", "45–54 anos", "55+ anos"]
    faixas = pd.cut(idades, bins=bins, labels=labels, right=True)
    df["FaixaEtaria"] = faixas.astype(str).replace(["nan", "NaN", "<NA>"], "Não informado")
    return df

def classificar_status(row) -> str:
    """Classificação determinística dos 4 status executivos."""
    col_contrato = "Situacao do contrato" if "Situacao do contrato" in row else "Situação do contrato"
    contrato = str(row.get(col_contrato, "")).strip().upper()

    if contrato in ["VIGENTE", "ATIVO"]:
        return "ATIVO"
    elif contrato in ["TRANCADO"]:
        return "TRANCADO"
    elif contrato in ["DESISTENTE", "DESISTENCIA", "DESISTÊNCIA"]:
        return "DESISTENTE"
    else:
        return "INATIVO"
    
def calcular_score_evasao(row, mapping: Dict[str, Optional[str]]) -> tuple[int, str]:
    """
    Calcula um score de risco de evasão (0 a 100) para discentes ativos
    e retorna o nível de risco e os fatores identificados.
    """
    if str(row.get("StatusDashboard", "")).upper() != "ATIVO":
        return 0, "Baixo"

    score = 0
    
    # 1. Indicador PcD / Necessidade de Acessibilidade (+30 pts)
    col_def = mapping.get("deficiencia")
    if col_def and str(row.get(col_def, "")).strip().upper() not in ["", "NÃO", "NAO", "NENHUMA", "NÃO INFORMADO", "NAN", "NONE"]:
        score += 30

    # 2. Forma de Ingresso com histórico de mobilidade/atrito (+25 pts)
    col_ing = mapping.get("ingresso")
    if col_ing and row.get(col_ing) in ["Transferência", "Reingresso / Reabertura", "Segunda Graduação / Portador de Diploma"]:
        score += 25

    # 3. Faixa Etária de maior vulnerabilidade a conciliação trabalho/estudo (+20 pts)
    faixa = str(row.get("FaixaEtaria", ""))
    if faixa in ["35–44 anos", "45–54 anos", "55+ anos"]:
        score += 20

    # 4. Situação Contratual com observações ou pendências (+25 pts)
    col_contrato = mapping.get("contrato")
    if col_contrato:
        contrato_txt = str(row.get(col_contrato, "")).upper()
        if any(term in contrato_txt for term in ["PENDENTE", "REABERTO", "CONDICIONAL", "RENOVAÇÃO", "RENOVACAO"]):
            score += 25

    score = min(score, 100)

    if score >= 60:
        nivel = "Crítico"
    elif score >= 35:
        nivel = "Moderado"
    else:
        nivel = "Baixo"

    return score, nivel