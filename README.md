# Dashboard de Gestão Acadêmica e Monitoramento de Evasão

Sistema web interativo para monitoramento contínuo de retenção discente, análise sociodemográfica e suporte à tomada de decisão pedagógica e administrativa da **Faculdade Uníntese**.

O projeto foi desenvolvido no âmbito do componente curricular de **Práticas Transdisciplinares de Ensino, Pesquisa e Extensão** do Curso Superior de Tecnologia em **Análise e Desenvolvimento de Sistemas**.

---

## 1. Visão Geral

O sistema substitui o controle manual e fragmentado de planilhas eletrônicas por um ecossistema analítico automatizado em nuvem. A aplicação realiza a extração de dados em tempo real via **Google Sheets API**, processa rotinas de higienização e engenharia de dados (_Data Wrangling_) em **Python**, persiste credenciais com hash criptográfico em **SQLite3** e disponibiliza visualizações analíticas em **Dark Mode** estruturadas sobre **Streamlit** e **Plotly**.

### Principais Funcionalidades

- **Autenticação e Controle de Acesso:** Módulo de login com criptografia por hash seguro (SHA-256) e gerenciamento de sessão via `st.session_state`.
- **Integração em Nuvem:** Leitura assíncrona de planilhas institucionais via Conta de Serviço (_Service Account_) utilizando o protocolo OAuth2 / JWT.
- **Diagnóstico de Retenção Discente:** Classificação determinística em quatro categorias executivas (_Ativo_, _Inativo_, _Desistente_ e _Trancado_).
- **Matriz Cruzada Contratual:** Cruzamento entre situação de contrato e situação acadêmica para identificação e triagem de discentes aptos a campanhas de rematrícula.
- **Módulo de Acessibilidade:** Filtros e indicadores voltados ao suporte a discentes com necessidades educacionais especiais ou deficiência declarada.
- **Inteligência Geográfica:** Mapeamento coroplético da densidade de discentes por Unidade Federativa integrado via GeoJSON.
- **Perfil Demográfico e Faixa Etária:** Algoritmo vetorizado de conversão de datas seriais do Excel para cálculo cronológico exato e categorização etária.
- **Exportação Dupla de Relatórios:** Geração e download sob demanda de bases filtradas nos formatos **CSV (UTF-8-SIG)** e **Excel (.xlsx)** utilizando buffers de memória (`BytesIO`).

---

## 2. Tecnologias Utilizadas

| Camada                          | Tecnologias / Bibliotecas                                            |
| :------------------------------ | :------------------------------------------------------------------- |
| **Linguagem Principal**         | Python 3.10+                                                         |
| **Interface e Visualização**    | Streamlit, Plotly Express, HTML5 / CSS3 customizado (_Dark Mode_)    |
| **Engenharia de Dados**         | Pandas, OpenPyXL, PyArrow                                            |
| **Segurança e Banco de Dados**  | SQLite3, Hashlib (SHA-256)                                           |
| **Integração e Nuvem**          | Google Cloud Platform (Google Sheets API e Google Drive API), OAuth2 |
| **Deploy e Controle de Versão** | Streamlit Community Cloud, Git / GitHub                              |

---

## 3. Indicadores e Métricas do Sistema

O sistema foi homologado em ambiente de produção com a base institucional completa:

- **Total de Discentes Monitorados:** 7.917 alunos
- **Alunos Ativos (Contrato Vigente):** 3.320 (41,9%)
- **Inativos Gerais:** 3.123 (39,4%)
- **Desistentes Formais:** 1.342 (17,0%)
- **Matrículas Trancadas:** 132 (1,7%)
- **Alunos com Deficiência / Acessibilidade:** 838 discentes (10,6% da base total)
- **Principais Estados em Densidade:** São Paulo (1.985), Minas Gerais (910), Rio Grande do Sul (883), Rio de Janeiro (807) e Bahia (407).

---

## 4. Estrutura do Repositório

```bash
dashboard-alunos/
├── app.py                     # Ponto de entrada da aplicação e interface Streamlit
├── services/
│   ├── auth.py                # Gerenciamento do banco SQLite e hash de senhas
│   └── google_sheets.py       # Conexão autenticada via Google Sheets API (OAuth2)
├── utils/
│   └── tratamento.py          # Regras de negócio, classificação de status e datas
├── data/
│   └── usuarios.db            # Banco de dados local SQLite (ignorado no Git)
├── .streamlit/
│   └── secrets.toml           # Credenciais e chaves GCP (ignorado no Git)
├── requirements.txt           # Dependências do projeto
├── .gitignore                 # Configuração de arquivos ignorados e proteção de segredos
└── README.md                  # Documentação técnica do projeto
5. Instalação e Execução Local
Pré-requisitos
Python 3.10 ou superior instalado.

Git instalado.

Projeto configurado no Google Cloud Platform com a Google Sheets API habilitada e chave de Conta de Serviço (Service Account) exportada em formato JSON.

Passo 1: Clonar o Repositório
Bash
git clone [https://github.com/Pietroks/dashboard-alunos.git](https://github.com/Pietroks/dashboard-alunos.git)
cd dashboard-alunos
Passo 2: Configurar o Ambiente Virtual
Bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / MacOS
python3 -m venv venv
source venv/bin/activate
Passo 3: Instalar as Dependências
Bash
pip install -r requirements.txt
Passo 4: Configurar as Credenciais (secrets.toml)
Crie o arquivo .streamlit/secrets.toml na raiz do projeto contendo as credenciais da Conta de Serviço e o identificador da planilha:

Ini, TOML
[gcp_service_account]
type = "service_account"
project_id = "seu-project-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "seu-email@seu-projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "[https://www.googleapis.com/robot/v1/metadata/x509/](https://www.googleapis.com/robot/v1/metadata/x509/)..."

[planilha]
id = "ID_DA_SUA_PLANILHA_GOOGLE_SHEETS"
Passo 5: Executar a Aplicação
Bash
streamlit run app.py
O painel estará disponível localmente em http://localhost:8501.

6. Segurança e Conformidade (LGPD)
As credenciais de produção e chaves privadas RSA são gerenciadas exclusivamente por variáveis de ambiente criptografadas (Streamlit Secrets), garantindo que informações confidenciais não sejam versionadas no repositório público.

A persistência de senhas segue o padrão de resumo criptográfico unidirecional via algoritmo SHA-256.

7. Autoria e Orientação
Desenvolvedor: Pietro Kettner da Silva — Acadêmico do Curso de Análise e Desenvolvimento de Sistemas (pietrokettner52@gmail.com)

Orientador: Prof. Pedro Stieler — Diretor e Coordenador Institucional (adm@unintese.com)

Instituição: Faculdade Uníntese

8. Licença
Este projeto foi desenvolvido para fins acadêmicos e institucionais sob a licença MIT.
```
