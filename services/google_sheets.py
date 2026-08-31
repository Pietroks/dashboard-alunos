import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

def carregar_planilha():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]
    
    creds = Credentials.from_service_account_file(
        "dashboard-alunos-494616-c0f5bcecc791.json",
        scopes=scope
    )
    
    client = gspread.authorize(creds)
    
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JzrYUvMCCAbzX0jGwgO16p1tKeOYK5yNXiPj8zPRwKs/edit?gid=787544599#gid=787544599")
    worksheet = sheet.sheet1
    
    data = worksheet.get_all_records()
    
    df = pd.DataFrame(data)
    
    return df