import sys

# Com argumentos, o backend vira CLI / servidor MCP (headless, sem HTTP).
# Sem argumentos (caso do Electron), sobe o servidor HTTP como sempre.
# O despacho vem antes das importações pesadas (fastapi, markitdown...).
if __name__ == "__main__" and len(sys.argv) > 1:
    from cli import main as _cli_main
    sys.exit(_cli_main(sys.argv[1:]))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.converter import build_markitdown, convert_file as core_convert_file
import tempfile
import os
import sys

import traceback
from typing import Optional

app = FastAPI(title="MarkItDown API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://0.0.0.0:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Header

@app.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    llm_api_key: Optional[str] = Form(None),
    llm_model: Optional[str] = Form(None),
    llm_base_url: Optional[str] = Form(None),
    target_format: Optional[str] = Form("md"),
    llm_provider: Optional[str] = Form("openai"),
    authorization: Optional[str] = Header(None)
):
    expected_token = os.environ.get("KHAT_TOKEN")
    if expected_token:
        if not authorization or authorization != f"Bearer {expected_token}":
            raise HTTPException(status_code=403, detail="Acesso local não autorizado")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        md = build_markitdown(llm_provider, llm_api_key, llm_model, llm_base_url)
    except Exception as e:
        error_details = traceback.format_exc()
        print("ERROR INITIALIZING MARKITDOWN:\n", error_details)
        raise HTTPException(status_code=500, detail="Failed to initialize MarkItDown: " + str(e))

    temp_files_to_delete = []
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            temp_files_to_delete.append(temp_file_path)
            
        return core_convert_file(
            temp_file_path, target_format, md,
            llm_provider=llm_provider, llm_api_key=llm_api_key,
            llm_model=llm_model, llm_base_url=llm_base_url,
        )

    except Exception as e:
        error_details = traceback.format_exc()
        print("ERROR IN CONVERSION:\n", error_details)
        error_msg = str(e)
        if hasattr(e, '__cause__') and e.__cause__:
            error_msg += f" (Cause: {e.__cause__})"
        
        snippet = error_details.split('\n')[-2] if len(error_details.split('\n')) > 1 else ""
        raise HTTPException(status_code=500, detail=error_msg + " | " + snippet)
    finally:
        for f in temp_files_to_delete:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
