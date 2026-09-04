import duckdb
import pandas as pd
from typing import Dict, List, Any

conn = duckdb.connect(database=":memory:")
# Limita o uso de RAM para não derrubar a instância compartilhada (ex: Streamlit Cloud com 1 GB de limite)
conn.execute("SET max_memory = '512MB';")
conn.execute("SET threads = 2;")

def consultar_dados_duckdb(
    parquet_path: str,
    filtros: Dict[str, List[Any]],
    busca: str = "",
    mapping: Dict[str, Any] = None
) -> pd.DataFrame:
    """
    Executa consulta SQL colunar de alta performance via DuckDB
    diretamente sobre o arquivo Parquet sem sobrecarregar a memória RAM.
    """
    conn = duckdb.connect(database=":memory:")
    
    condicoes = ["1=1"]
    parametros = []

    # 1. Filtro de busca textual (Nome ou Matrícula)
    if busca and mapping:
        termos_busca = []
        col_nome = mapping.get("nome")
        col_matr = mapping.get("matricula")
        
        if col_nome:
            termos_busca.append(f"lower(CAST(\"{col_nome}\" AS VARCHAR)) LIKE ?")
            parametros.append(f"%{busca.lower()}%")
        if col_matr:
            termos_busca.append(f"lower(CAST(\"{col_matr}\" AS VARCHAR)) LIKE ?")
            parametros.append(f"%{busca.lower()}%")
            
        if termos_busca:
            condicoes.append(f"({' OR '.join(termos_busca)})")

    # 2. Filtros categóricos dinâmicos da barra lateral
    for coluna, valores in filtros.items():
        if valores:
            placeholders = ", ".join(["?"] * len(valores))
            condicoes.append(f"CAST(\"{coluna}\" AS VARCHAR) IN ({placeholders})")
            parametros.extend([str(v) for v in valores])

    clausula_where = " AND ".join(condicoes)
    sql = f"SELECT * FROM read_parquet(?) WHERE {clausula_where}"
    
    try:
        # read_parquet é passado como o primeiro parâmetro para o DuckDB
        todos_parametros = [parquet_path] + parametros
        resultado_df = conn.execute(sql, todos_parametros).fetchdf()
        return resultado_df
    finally:
        conn.close()