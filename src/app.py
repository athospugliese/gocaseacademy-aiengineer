# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
import shutil
import logging
from pathlib import Path
import sys
import uuid

# Import our PDI generator agent
from pdi_agent import executar_fluxo

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="GoCase PDI Generator API",
    description="API para geração automática de Planos de Desenvolvimento Individual (PDI)",
    version="1.0.0"
)

# Create a directory to store temporary files
TEMP_DIR = Path("./temp")
TEMP_DIR.mkdir(exist_ok=True)

@app.post("/generate-pdi/", summary="Generate PDI from Excel file")
async def generate_pdi(file: UploadFile = File(...)):
    """
    Upload an Excel file with performance evaluation data and receive a PDF with PDI suggestions.
    
    The Excel file must contain the following sheets:
    - Notas: Contains criteria and final scores
    - Gestor: Contains manager feedback
    - Colaborador: Contains employee self-evaluation
    """
    try:
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        temp_dir = TEMP_DIR / request_id
        temp_dir.mkdir(exist_ok=True)
        
        # Save the uploaded file
        excel_path = temp_dir / file.filename
        with open(excel_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {excel_path}")
        
        # Process the file with our agent
        df_resultado, pdf_path = executar_fluxo(str(excel_path))
        
        if not df_resultado is not None and not pdf_path:
            raise HTTPException(status_code=500, detail="Failed to generate PDI")
        
        # Move the generated PDF to our temp directory
        output_pdf = temp_dir / "PDI_gerado.pdf"
        shutil.copy(pdf_path, output_pdf)
        
        # Return the PDF file
        return FileResponse(
            path=output_pdf,
            filename="PDI_gerado.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up will be handled by a background task
        pass

@app.on_event("shutdown")
def cleanup_temp_files():
    """Remove temporary files on shutdown"""
    try:
        shutil.rmtree(TEMP_DIR)
        logger.info("Temporary files cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up temporary files: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)