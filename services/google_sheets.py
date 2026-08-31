import os
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
    
    # 1. Se estiver rodando localmente com arquivo físico
    if os.path.exists(caminho_local):
        creds = Credentials.from_service_account_file(
            caminho_local,
            scopes=scope
        )
    # 2. Se estiver no Streamlit Cloud
    elif "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        # Garante que os \n na chave privada sejam quebras de linha reais
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
        creds = Credentials.from_service_account_info(
            info,
            scopes=scope
        )
    else:
        raise ValueError("Credenciais do Google não encontradas (nem arquivo local nem st.secrets).")
    
    client = gspread.authorize(creds)
    
    # ID da sua planilha
    SPREADSHEET_ID = "1JzrYUvMCCAbzX0jGwgO16p1tKeOYK5yNXiPj8zPRwKs"
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.get_worksheet(0)  # Primeira aba
    
    # Lê todos os valores de forma segura
    valores = worksheet.get_all_values()
    if not valores or len(valores) < 2:
        return pd.DataFrame()
        
    cabecalho = valores[0]
    linhas = valores[1:]
    
    df = pd.DataFrame(linhas, columns=cabecalho)
    return df