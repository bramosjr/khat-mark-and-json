from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from markitdown import MarkItDown
import tempfile
import os
import traceback
from typing import Optional

app = FastAPI(title="MarkItDown API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    llm_api_key: Optional[str] = Form(None),
    llm_model: Optional[str] = Form("gpt-4o")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        if llm_api_key and llm_api_key.strip():
            from openai import OpenAI
            client = OpenAI(api_key=llm_api_key.strip())
            md = MarkItDown(llm_client=client, llm_model=llm_model)
        else:
            md = MarkItDown()
    except Exception as e:
        error_details = traceback.format_exc()
        print("ERROR INITIALIZING MARKITDOWN:\n", error_details)
        raise HTTPException(status_code=500, detail="Failed to initialize MarkItDown: " + str(e))

    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        result = md.convert(temp_file_path)
        
        return {"markdown": result.text_content}
        
    except Exception as e:
        error_details = traceback.format_exc()
        print("ERROR IN CONVERSION:\n", error_details)
        error_msg = str(e)
        if hasattr(e, '__cause__') and e.__cause__:
            error_msg += f" (Cause: {e.__cause__})"
        
        snippet = error_details.split('\n')[-2] if len(error_details.split('\n')) > 1 else ""
        raise HTTPException(status_code=500, detail=error_msg + " | " + snippet)
    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
