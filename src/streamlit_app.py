# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import io
import base64
import time
import os

# Set page configuration
st.set_page_config(
    page_title="GoCase - Gerador de PDI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint
API_URL = os.getenv("API_URL", "http://localhost:8000/generate-pdi/")

def main():
    # Header
    st.markdown(
      """
      <style>
      .fixed-size-image img {
          width: 424px !important;
          height: 120px !important;
          object-fit: contain;
      }
      </style>
      """,
      unsafe_allow_html=True
  )

  # Exibir a imagem com a classe CSS personalizada
    st.markdown(
          """
          <div class="fixed-size-image">
              <img src="https://www.overloadgames.com.br/img/parceiros/gocase/gocase.png">
          </div>
          """,
          unsafe_allow_html=True
      )

    st.title("🚀 Gerador Automático de PDI")
    st.markdown("""
    ### Otimização do processo de avaliação de desempenho
    
    Este sistema utiliza inteligência artificial para analisar dados de avaliação de desempenho
    e gerar Planos de Desenvolvimento Individual (PDI) personalizados.
    """)
    
    # File uploader
    st.header("📤 Upload do Arquivo de Avaliação")
    
    with st.expander("ℹ️ Instruções", expanded=True):
        st.markdown("""
        1. Prepare seu arquivo Excel com as seguintes planilhas:
           - **Notas**: Contendo os critérios e pontuações finais
           - **Gestor**: Contendo o feedback do gestor
           - **Colaborador**: Contendo a autoavaliação
        2. Faça o upload do arquivo abaixo
        3. Clique em "Gerar PDI" e aguarde o processamento
        4. Faça o download do PDF gerado
        """)
    
    uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
    
    if uploaded_file is not None:
        # Show preview of the uploaded file
        try:
            xls = pd.ExcelFile(uploaded_file)
            tabs = st.tabs(xls.sheet_names)
            
            for i, sheet_name in enumerate(xls.sheet_names):
                with tabs[i]:
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                    st.dataframe(df, use_container_width=True)
            
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            
            # Process button
            if st.button("🔄 Gerar PDI", type="primary"):
                with st.spinner("Processando... Isso pode levar alguns instantes."):
                    # Prepare file for API request
                    files = {"file": uploaded_file}
                    
                    try:
                        # Send request to API
                        response = requests.post(API_URL, files=files)
                        
                        if response.status_code == 200:
                            # Get PDF content
                            pdf_content = response.content
                            
                            # Create download button
                            st.success("✅ PDI gerado com sucesso!")
                            
                            # Create download link for PDF
                            b64_pdf = base64.b64encode(pdf_content).decode()
                            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="PDI_gerado.pdf" class="download-button">📥 Download do PDI (PDF)</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                            # Apply custom CSS for download button
                            st.markdown("""
                            <style>
                            .download-button {
                                display: inline-block;
                                padding: 0.5em 1em;
                                background-color: #4CAF50;
                                color: white;
                                text-align: center;
                                text-decoration: none;
                                font-size: 16px;
                                margin: 4px 2px;
                                border-radius: 4px;
                                cursor: pointer;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            # Show PDF preview (embedded)
                            st.subheader("📄 Prévia do PDI")
                            st.markdown(f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)
                            
                        else:
                            st.error(f"❌ Erro ao processar o arquivo: {response.text}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro de conexão: {str(e)}")
                        st.info("Verifique se o servidor da API está funcionando corretamente.")
        
        except Exception as e:
            st.error(f"❌ Erro ao ler o arquivo: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.caption("© 2025 Universo GoCase | Desenvolvido por Athos Pugliese para otimização de processos de RH")

if __name__ == "__main__":
    main()