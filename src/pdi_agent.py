# pdi_agent.py
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Union
import logging
import sys
from fpdf import FPDF

# Configurar logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    dados_brutos: pd.ExcelFile
    dados_processados: pd.DataFrame
    pdi_final: pd.DataFrame
    notas: pd.DataFrame
    gestor: pd.DataFrame
    colaborador: pd.DataFrame
    input: str

# Carregar variáveis de ambiente
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0)

def debug_dataframe(df: pd.DataFrame, name: str):
    """Função auxiliar para debug de DataFrames"""
    logger.info(f"\nDebug {name}:")
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Colunas: {df.columns.tolist()}")
    logger.info(f"Primeiras linhas:\n{df.head(2)}")
    logger.info("-" * 50)

def carregar_dados(state: AgentState):
    """Carrega os dados do arquivo Excel com validação"""
    try:
        logger.info(f"Iniciando carregamento de dados...")
        
        xls = pd.ExcelFile(state['input'])
        logger.info(f"Planilhas encontradas: {xls.sheet_names}")
        
        # Carregar com nomes explícitos
        notas_df = pd.read_excel(xls, sheet_name="Notas")
        
        # Carregar planilha do Gestor e renomear colunas corretamente
        avaliacao_gestor_df = pd.read_excel(xls, sheet_name="Gestor")
        if 'Unnamed: 1' in avaliacao_gestor_df.columns:
            avaliacao_gestor_df = avaliacao_gestor_df.rename(columns={'Unnamed: 1': 'Feedback do Gestor'})
        
        # Carregar planilha do Colaborador e renomear colunas corretamente
        autoavaliacao_df = pd.read_excel(xls, sheet_name="Colaborador")
        if 'Unnamed: 1' in autoavaliacao_df.columns:
            autoavaliacao_df = autoavaliacao_df.rename(columns={'Unnamed: 1': 'Autoavaliação Texto'})
        
        # Debug
        debug_dataframe(notas_df, "Notas")
        debug_dataframe(avaliacao_gestor_df, "Gestor")
        debug_dataframe(autoavaliacao_df, "Colaborador")
        
        return {
            "dados_brutos": xls,
            "notas": notas_df,
            "gestor": avaliacao_gestor_df,
            "colaborador": autoavaliacao_df
        }
        
    except Exception as e:
        logger.error(f"Erro no carregamento: {str(e)}")
        raise

def analisar_desempenho(state: AgentState):
    """Processa os dados com verificações de consistência"""
    try:
        logger.info("Iniciando análise de desempenho...")
        
        df = state['notas'].copy()
        
        # Verificar colunas
        cols_necessarias = ['Criterios', 'Pontuação final']
        if not all(col in df.columns for col in cols_necessarias):
            raise ValueError("Colunas ausentes na planilha de Notas")
        
        # Corrigir índices para mesclar os dataframes
        # Vamos usar a coluna Criterios como índice
        gestor_df = state['gestor'].copy()
        if 'Avaliação do Gestor' in gestor_df.columns:
            criterios_gestor = gestor_df['Avaliação do Gestor'].tolist()
            feedback_gestor = gestor_df['Feedback do Gestor'].tolist()
            
            # Criar dicionário de feedback do gestor
            feedback_dict = dict(zip(criterios_gestor, feedback_gestor))
            
            # Adicionar coluna de feedback na planilha de notas
            df['Feedback do Gestor'] = df['Criterios'].map(feedback_dict)
        
        # Fazer o mesmo para autoavaliação
        colab_df = state['colaborador'].copy()
        if 'Autoavaliação' in colab_df.columns:
            criterios_colab = colab_df['Autoavaliação'].tolist()
            texto_colab = colab_df['Autoavaliação Texto'].tolist()
            
            # Criar dicionário de autoavaliação
            autoav_dict = dict(zip(criterios_colab, texto_colab))
            
            # Adicionar coluna de autoavaliação na planilha de notas
            df['Autoavaliação Texto'] = df['Criterios'].map(autoav_dict)
        
        # Análise
        df["Ponto Forte"] = df["Pontuação final"] >= 3.5
        df["Área de Melhoria"] = df["Pontuação final"] < 3
        
        debug_dataframe(df, "Dados Analisados")
        
        return {"dados_processados": df}
        
    except Exception as e:
        logger.error(f"Erro na análise: {str(e)}")
        raise

def gerar_pdi(state: AgentState):
    """Gera PDI com tratamento de erros"""
    try:
        logger.info("Iniciando geração de PDI...")
        
        df = state['dados_processados'].copy()
        resultados = []
        
        for idx, row in df.iterrows():
            logger.info(f"Processando critério {idx+1}/{len(df)}...")
            
            # Adaptar para usar os novos nomes de colunas
            autoav_texto = row.get('Autoavaliação Texto', 'Não disponível')
            feedback_gestor = row.get('Feedback do Gestor', 'Não disponível')
            
            prompt = f"""
            ## Contexto:
            Você é um especialista em RH da GoCase. Analise os seguintes dados e sugira um plano de desenvolvimento:

            **Critério**: {row['Criterios']}
            **Pontuação**: {row['Pontuação final']}
            **Feedback Gestor**: {feedback_gestor}
            **Autoavaliação**: {autoav_texto}

            ## Instruções:
            1. Identifique 1 ponto forte
            2. Aponte 1 área de melhoria
            3. Sugira 2 ações concretas
            4. Recomende 1 indicador de evolução
            """
            
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                resultados.append(response.content)
                logger.debug(f"Resposta LLM: {response.content[:100]}...")  # Log parcial
                
            except Exception as e:
                logger.warning(f"Erro na geração para critério {row['Criterios']}: {str(e)}")
                resultados.append("Erro na geração")
        
        df["PDI Sugerido"] = resultados
        debug_dataframe(df, "Resultado Final")
        
        return {"pdi_final": df}
        
    except Exception as e:
        logger.error(f"Erro geral no PDI: {str(e)}")
        raise

def exportar_para_pdf(df, nome_arquivo="PDI_gerado.pdf"):
    """Exporta apenas os PDIs sugeridos para um arquivo PDF formatado"""
    try:
        logger.info(f"Iniciando exportação para PDF: {nome_arquivo}")
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Configurar fontes
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Plano de Desenvolvimento Individual (PDI)", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "GoCase - Avaliação de Desempenho", ln=True, align="C")
        pdf.ln(10)
        
        # Para cada critério, adicionar sua seção no PDF
        for idx, row in df.iterrows():
            # Título do Critério
            pdf.set_font("Arial", "B", 12)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 10, f"Critério: {row['Criterios']}", ln=True, fill=True)
            
            # Pontuação
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 10, f"Pontuação: {row['Pontuação final']}", ln=True)
            
            # PDI Sugerido
            pdf.set_font("Arial", "", 10)
            
            # Dividir o texto do PDI em linhas para melhor formatação
            pdi_text = row['PDI Sugerido']
            
            # Verificar se o texto não está vazio
            if pdi_text and pdi_text != "Erro na geração":
                # Adicionar texto do PDI com quebras de linha apropriadas
                pdf.multi_cell(0, 6, pdi_text)
            else:
                pdf.cell(0, 10, "PDI não disponível para este critério", ln=True)
            
            # Adicionar separador
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(10)
            
            # Verificar se uma nova página é necessária
            if pdf.get_y() > 250:
                pdf.add_page()
        
        # Salvar o PDF
        pdf.output(nome_arquivo)
        logger.info(f"PDF gerado com sucesso: {nome_arquivo}")
        return nome_arquivo
        
    except Exception as e:
        logger.error(f"Erro na exportação para PDF: {str(e)}")
        raise

# Configurar o fluxo
workflow = StateGraph(AgentState)

workflow.add_node("carregar_dados", carregar_dados)
workflow.add_node("analisar_desempenho", analisar_desempenho)
workflow.add_node("gerar_pdi", gerar_pdi)

workflow.set_entry_point("carregar_dados")
workflow.add_edge("carregar_dados", "analisar_desempenho")
workflow.add_edge("analisar_desempenho", "gerar_pdi")
workflow.add_edge("gerar_pdi", END)

app = workflow.compile()

# Função de execução melhorada
def executar_fluxo(arquivo_xlsx: str):
    """Executa o fluxo completo com tratamento de erros e exporta para PDF"""
    try:
        logger.info(f"Iniciando processamento do arquivo: {arquivo_xlsx}")
        
        inputs = {"input": arquivo_xlsx}
        resultados = app.invoke(inputs)
        
        if 'pdi_final' in resultados:
            df = resultados['pdi_final']
            logger.info("Processamento concluído com sucesso!")
            logger.info(f"Total de registros processados: {len(df)}")
            
            # Exportar apenas o PDI sugerido para PDF
            pdf_path = exportar_para_pdf(df)
            logger.info(f"PDF salvo em: {pdf_path}")
            
            return df, pdf_path
        else:
            logger.error("Fluxo não retornou resultados esperados")
            return None, None
            
    except Exception as e:
        logger.error(f"Erro no fluxo principal: {str(e)}")
        return None, None