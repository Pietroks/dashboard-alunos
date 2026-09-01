# Dashboard de Gestão Acadêmica | Uníntese

Painel analítico e institucional para monitoramento de discentes, acompanhamento de taxas de retenção/evasão e análise demográfica a partir de dados integrados via Google Sheets.

---

## Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit** (Interface e orquestração web)
- **Pandas** (Tratamento, agregação e limpeza de dados)
- **Plotly Express** (Visualizações gráficas interativas e mapas coropléticos)
- **gspread & Google OAuth2** (Integração segura com Google Sheets API)
- **SQLite3 & Hashlib (SHA-256)** (Autenticação e controle de acesso)
- **OpenPyXL** (Exportação de relatórios em Excel `.xlsx`)

---

## Estrutura do Projeto

```text
dashboard_alunos/
├── app.py                      # Ponto de entrada e fluxo principal da aplicação
├── components/
│   ├── charts.py               # Gráficos Plotly, mapas GeoJSON e formatações visuais
│   └── views.py                # Componentes de interface (Login, Sidebar, Métricas, Matrizes)
├── services/
│   ├── auth.py                 # Banco SQLite, criação de tabelas e validação de login
│   └── google_sheets.py        # Conexão híbrida (Local via JSON / Nuvem via st.secrets)
├── utils/
│   ├── styles.py               # CSS customizado, tema Dark Mode e paleta de cores
│   └── tratamento.py           # Normalização de dados, mapeamento O(1), status e faixas etárias
├── requirements.txt            # Dependências do projeto
├── .gitignore                  # Proteção de credenciais locais e cache
└── README.md                   # Documentação do projeto
Funcionalidades PrincipaisAcesso Seguro & Sessão Persistente:Tela de login institucional com credenciais armazenadas via hash SHA-256.Manutenção de login ativo via token de sessão (resistente ao F5/recarregamento).Limpeza e Normalização Categórica:Forma de Ingresso: Agrupamento de variações de texto (ex: Enem, nota do enem $\rightarrow$ ENEM).Cor/Raça & Escolaridade: Remoção de acentos e padronização automática de caixa alta/baixa.Engenharia de Datas: Tratamento vetorizado de números de série do Excel e strings textuais para cálculo dinâmico de faixas etárias.Preservação de Tipagem: Conversão e higienização seletiva focada em colunas textuais, preservando dados numéricos e IDs.Métricas e Indicadores Executivos:Cards de volume: Total, Ativos, Trancados, Inativos e Desistentes.Indicadores percentuais de retenção acadêmica.Matriz cruzada de contingência: Situação do Contrato $\times$ Situação do Aluno.Visualizações Interativas (Plotly Dark Mode):Gráficos de barras horizontais com truncamento de rótulos e nomes completos no tooltip (hover).Abas (Tabs) organizadas para análise de Cursos e Turmas.Gráficos de rosca (donut) para Ingresso, Sexo e Acessibilidade.Mapa coroplético de densidade discente por estados brasileiros (GeoJSON).Busca e Filtros Dinâmicos:Busca textual simultânea por Nome e Matrícula via operadores lógicos seguros.Filtros combinados via barra lateral retrátil com botão de reabertura persistente.Exportação de Dados:Download imediato da base filtrada nos formatos CSV (UTF-8 com BOM) e Excel (.xlsx).🛠️ Como Executar Localmente1. Clonar o repositórioBashgit clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd dashboard_alunos
2. Criar e ativar o ambiente virtualNo Windows (PowerShell):PowerShellpython -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned ; .\venv\Scripts\Activate.ps1
No Linux/macOS:Bashpython3 -m venv venv
source venv/bin/activate
3. Instalar as dependênciasBashpip install -r requirements.txt
4. Configurar as credenciais do Google CloudColoque o seu arquivo .json de Conta de Serviço (Service Account) na raiz do projeto com o padrão:dashboard-alunos-*.json(O código detecta automaticamente qualquer arquivo JSON de credenciais presente na pasta).5. Iniciar a aplicaçãoBashstreamlit run app.py
O painel abrirá automaticamente em seu navegador padrão no endereço http://localhost:8501.☁️ Deploy no Streamlit Community CloudPara publicar na nuvem:Faça o push do projeto para o GitHub:Bashgit add .
git commit -m "Deploy: Dashboard Acadêmico Otimizado"
git push origin main
Acesse share.streamlit.io e conecte o repositório.No painel de Secrets do app, insira as credenciais do Google Cloud no formato TOML:Ini, TOML[gcp_service_account]
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
SegurançaO arquivo .gitignore já está configurado para não subir chaves .json, arquivos secrets.toml, bancos de dados .db locais ou pastas temporárias de ambiente (venv/, __pycache__/).
```
