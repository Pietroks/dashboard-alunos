import os
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def carregar_planilha():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]
    
    caminho_local = "dashboard-alunos-494616-c0f5bcecc791.json"
    
    # 1. Se estiver rodando localmente e o arquivo JSON existir na pasta
    if os.path.exists(caminho_local):
        creds = Credentials.from_service_account_file(
            caminho_local,
            scopes=scope
        )
    # 2. Se estiver rodando na nuvem (Streamlit Cloud), lê dos Secrets seguros
    else:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
    
    client = gspread.authorize(creds)
    
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JzrYUvMCCAbzX0jGwgO16p1tKeOYK5yNXiPj8zPRwKs/edit?gid=787544599#gid=787544599")
    worksheet = sheet.sheet1
    
    data = worksheet.get_all_records()
    
    df = pd.DataFrame(data)
    
    return df