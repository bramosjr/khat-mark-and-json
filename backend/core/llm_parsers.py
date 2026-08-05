from core.output_wrapper import format_json_output
import json

def parse_with_llm(file_path: str, provider: str, api_key: str) -> dict:
    """
    Extrai o conteúdo bruto de um arquivo (PDF ou doc antigo) e o roteia
    para um LLM de terceiros formatar as hierarquias e layouts de forma inteligente.
    """
    import fitz  # PyMuPDF
    
    # 1. Extração bruta ultrarrápida do conteúdo para mandar pro prompt
    doc = fitz.open(file_path)
    raw_text = chr(12).join([page.get_text() for page in doc])
    
    # Limitamos para evitar estourar contextos excessivamente, embora gemini suporte 1M.
    content_sample = raw_text[:30000] 
    
    prompt = (
        "Analise o texto estrutural a seguir extraído de um documento corporativo/governamental. "
        "Formate este texto de volta em um array JSON estrito, identificando hierarquicamente os títulos (H1, H2), "
        "parágrafos e formatando possíveis tabelas como objetos aninhados. "
        "O output deve ser *estritamente* um JSON e nada mais.\n\n"
        f"Texto:\n{content_sample}"
    )
    
    llm_extracted_json = None

    try:
        # 2. Roteamento de API
        if provider.lower() == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Gemini-1.5-flash é ultra rápido para parse
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            # Tentar processar a string como json (remover crases se o modelo formatou com markdown codeblock)
            raw_response = response.text.strip()
            if raw_response.startswith('```json'):
                raw_response = raw_response[7:-3].strip()
            elif raw_response.startswith('```'):
                raw_response = raw_response[3:-3].strip()
                
            llm_extracted_json = json.loads(raw_response)

        else: # Default OpenAI
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" } # Força json nativo se o modelo suportar
            )
            raw_response = response.choices[0].message.content.strip()
            llm_extracted_json = json.loads(raw_response)
            
    except Exception as e:
        raise ValueError(f"Erro ao processar com provedor {provider}: {str(e)}")

    return format_json_output({"source_type": f"pdf_llm_structured_{provider}", "pages_read": len(doc)}, [llm_extracted_json])
