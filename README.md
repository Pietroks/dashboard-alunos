# Dashboard de Gestão Acadêmica | Uníntese

Painel analítico e institucional de alta performance para monitoramento de discentes, acompanhamento de taxas de retenção/evasão, triagem preditiva de riscos e análise demográfica territorial.

---

## Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit** (Interface e orquestração web reativa)
- **DuckDB** (Motor analítico colunar SQL in-memory para filtragem vetorizada)
- **Apache Arrow / PyArrow & Parquet** (Armazenamento colunar persistente e cache local de alta performance)
- **Pandas** (Tratamento, higienização e engenharia de atributos)
- **Plotly Express & Plotly Graph Objects** (Visualizações interativas, Sankey, Funil e Mapas GeoJSON)
- **ReportLab** (Geração server-side de relatórios executivos e fichas cadastrais em PDF)
- **gspread & Google OAuth2** (Integração com Google Sheets API via Service Account)
- **SQLite3 & HMAC-SHA256** (Autenticação, RBAC e validação criptográfica de sessões)
- **OpenPyXL** (Exportação analítica em planilhas Excel `.xlsx`)

---

## Estrutura do Projeto

```text
dashboard_alunos/
├── app.py                      # Ponto de entrada, orquestração de rotas e ciclo de vida Streamlit
├── dados_snapshot.parquet      # Snapshot colunar persistente dos dados normalizados
├── components/
│   ├── charts.py               # Gráficos Plotly, Funil, Sankey Diagram, Coorte e Mapas GeoJSON
│   └── views.py                # Componentes de UI (Login HMAC, Sidebar, Métricas, Cards 360°, Tabelas)
├── services/
│   ├── auth.py                 # Banco SQLite, gerenciamento de credenciais e hashing
│   ├── google_sheets.py        # Conexão híbrida e resiliente com Google Drive / Sheets API
│   └── query_engine.py         # Camada analítica DuckDB para consultas SQL vetorizadas no Parquet
├── utils/
│   ├── relatorios.py           # Motores ReportLab (Ficha Individual 360° e Relatório de Diretoria em PDF)
│   ├── styles.py               # CSS customizado, tema Dark Mode e vetores SVG Lucide
│   └── tratamento.py           # Normalização categórica, cálculo de risco de evasão e cohorts
├── requirements.txt            # Dependências e bibliotecas do ecossistema
├── .gitignore                  # Proteção de credenciais, snapshots e segredos locais
└── README.md                   # Documentação arquitetural do projeto
Funcionalidades PrincipaisMotor Analítico com DuckDB + Parquet: As filtragens e buscas de texto rodam diretamente sobre arquivo .parquet via consultas SQL vetorizadas, garantindo latência de milissegundos sem sobrecarregar a memória RAM da aplicação.  Autenticação Segura & Sessão Blindada com HMAC: Autenticação via SQLite integrada com assinatura digital HMAC-SHA256 alimentada por chave privada em secrets.toml, garantindo persistência sem tela piscando no F5 e sem risco de falsificação de parâmetros.Matriz de Transição e Churn (Sankey Diagram): Mapeamento do fluxo dos estudantes: Forma de Ingresso $\rightarrow$ Classificação de Risco $\rightarrow$ Status Final, rastreando a origem de evasões e trancamentos.  Inteligência Preditiva de Risco de Evasão: Algoritmo ponderado de triagem discente que pontua vulnerabilidades (PcD, forma de ingresso, faixa etária e histórico) em níveis Crítico, Moderado e Baixo.  Visão Cadastral Discente 360°: Consulta individualizada por discente com ficha unificada e botão para download de documento formal em PDF formatado via ReportLab.  Funil de Retenção & Análise Cohort: Visualização em funil da permanência dos discentes e coortes temporais de sobrevivência de turmas por ano de ingresso.  Normalização Categórica Robusta: Higienização de formas de ingresso, cor/raça (padrão IBGE), escolaridade prévia e tratamento de datas seriais do Excel para cálculo dinâmico de faixas etárias.  Exportação Multiformato: Extração da base filtrada em CSV (UTF-8 com BOM), Excel .xlsx e Relatório Executivo Consolidado para Colegiado em PDF.  Como Executar Localmente1. Clonar o repositórioBashgit clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd dashboard_alunos
2. Criar e ativar o ambiente virtualWindows (PowerShell):PowerShellpython -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned ; .\venv\Scripts\Activate.ps1
Linux/macOS:Bashpython3 -m venv venv
source venv/bin/activate
3. Instalar as dependênciasBashpip install -r requirements.txt
4. Configurar as Chaves e SegredosCrie a pasta .streamlit/ e o arquivo .streamlit/secrets.toml na raiz do projeto:Ini, TOMLSECRET_SALT = "sua_chave_privada_longa_e_aleatoria_para_hmac"
Coloque o arquivo de Conta de Serviço do Google Cloud (dashboard-alunos-*.json) na raiz do projeto para a sincronização de dados.5. Iniciar a aplicaçãoBashstreamlit run app.py
Acesse no navegador: http://localhost:8501Deploy no Streamlit Community CloudRealize o commit e push do projeto para um repositório no GitHub (o .gitignore protegerá credenciais e snapshots locais).Conecte o repositório no share.streamlit.io.No painel de Secrets do app, insira os blocos com o SECRET_SALT e as credenciais do Google Cloud:Ini, TOMLSECRET_SALT = "sua_chave_privada_para_hmac_em_producao"

[gcp_service_account]
type = "service_account"
project_id = "seu-project-id"
private_key_id = "sua-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
SUA_CHAVE_PRIVADA_AQUI
-----END PRIVATE KEY-----"""
client_email = "seu-email@seu-projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "[https://www.googleapis.com/robot/v1/metadata/x509/](https://www.googleapis.com/robot/v1/metadata/x509/)..."
```
