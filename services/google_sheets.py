import os
import json
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def carregar_planilha():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    
    caminho_local = "dashboard-alunos-494616-c0f5bcecc791.json"
    
    # 1. Se estiver rodando localmente
    if os.path.exists(caminho_local):
        creds = Credentials.from_service_account_file(
            caminho_local,
            scopes=scope
        )
    # 2. Se estiver no Streamlit Cloud via string JSON bruta
    elif "gcp_json" in st.secrets:
        info = json.loads(st.secrets["gcp_json"])
        creds = Credentials.from_service_account_info(
            info,
            scopes=scope
        )
    else:
        raise ValueError("Credenciais 'gcp_json' não encontradas nos Secrets do Streamlit.")
    
    client = gspread.authorize(creds)
    
    SPREADSHEET_ID = "1JzrYUvMCCAbzX0jGwgO16p1tKeOYK5yNXiPj8zPRwKs"
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.get_worksheet(0)
    
    valores = worksheet.get_all_values()
    if not valores or len(valores) < 2:
        return pd.DataFrame()
        
    cabecalho = valores[0]
    linhas = valores[1:]
    
    df = pd.DataFrame(linhas, columns=cabecalho)
    return df