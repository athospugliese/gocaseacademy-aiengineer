# GoCase PDI Generator

Este sistema automatiza a geração de Planos de Desenvolvimento Individual (PDI) a partir de dados de avaliação de desempenho.

## Demonstração

https://github.com/user-attachments/assets/2cffbcf5-4b51-4a44-8947-03a26f48efb5



## Arquitetura

O sistema é composto por:

1. **API Backend (FastAPI)**: Processa os arquivos Excel e gera PDFs com os PDIs
2. **Frontend (Streamlit)**: Interface amigável para upload de arquivos e download dos PDIs
3. **Agente de IA**: Utiliza LangGraph e GPT-4 para analisar os dados e gerar sugestões personalizadas

## Requisitos

- Chave de API da OpenAI

## Configuração

1. Crie um arquivo `.env` na raiz do projeto com sua chave de API:

```
OPENAI_API_KEY=sua_chave_api_aqui
```

## Execução

### Sem Docker (desenvolvimento)

1. Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```
2. Execute dentro da pasta src\

3. Inicie o backend:

```bash
uvicorn app:app --reload --port 8000
```

4. Inicie o frontend:

```bash
streamlit run streamlit_app.py
```

5. Acesse o frontend em [http://localhost:8501](http://localhost:8501)

## Uso

1. Prepare um arquivo Excel com as planilhas:
   - **Notas**: Contendo os critérios e pontuações finais
   - **Gestor**: Contendo o feedback do gestor
   - **Colaborador**: Contendo a autoavaliação

2. Faça upload do arquivo na interface do Streamlit

3. Clique em "Gerar PDI"

4. Faça download do PDF gerado

## Estrutura de Arquivos

```
.
├── app.py                 # API FastAPI
├── pdi_agent.py           # Agente de IA para geração de PDI
├── streamlit_app.py       # Frontend Streamlit
├── requirements.txt   # Dependências do backend
└── .env                   # Variáveis de ambiente (não incluído)
```

