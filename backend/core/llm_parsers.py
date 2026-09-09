"""
Roteamento de provedores de LLM para extração/estruturação de documentos em
JSON. Nenhum provedor aqui tem um nome de modelo fixo no código — o nome do
modelo sempre vem de fora (do formulário do frontend). Isso é deliberado:
nomes de modelo de LLM ficam obsoletos rápido (ex.: 'gemini-1.5-flash'
hardcoded já não existia mais quando isso foi corrigido), então o código
nunca deve "adivinhar" um valor atual — ou o usuário informa, ou a função
falha com uma mensagem clara pedindo para informar, em vez de tentar um
modelo que pode não existir mais.
"""
from core.output_wrapper import format_json_output
import json


def _strip_markdown_json_fence(text: str) -> str:
    """Remove um bloco de código markdown (```json ... ``` ou ``` ... ```)
    em volta da resposta, se o modelo tiver formatado assim."""
    text = text.strip()
    if text.startswith('```json'):
        text = text[len('```json'):].strip()
    elif text.startswith('```'):
        text = text[3:].strip()
    if text.endswith('```'):
        text = text[:-3].strip()
    return text


def _require_model(model_name: str, provider_label: str) -> str:
    """Garante que um nome de modelo foi informado, sem tentar um valor
    padrão — modelos de LLM mudam com frequência demais para serem
    hardcoded com segurança aqui."""
    if not model_name or not model_name.strip():
        raise ValueError(
            f"Informe o nome do modelo do {provider_label} nas Configurações "
            "antes de converter (consulte a documentação atual do provedor "
            "para o nome exato do modelo)."
        )
    return model_name.strip()


def _call_gemini(prompt: str, api_key: str, model_name: str, base_url: str = None) -> str:
    # google-generativeai está descontinuado (o próprio pacote avisa:
    # "All support... has ended, switch to google.genai") — usa o pacote
    # novo, google-genai (`from google import genai`), com a API baseada em
    # client em vez do antigo genai.configure()/GenerativeModel().
    from google import genai

    model_name = _require_model(model_name, "Google Gemini")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model_name, contents=prompt)
    return _strip_markdown_json_fence(response.text)


def _call_openai(prompt: str, api_key: str, model_name: str, base_url: str = None) -> str:
    from openai import OpenAI

    # OpenAI é o único provedor com um default aqui — o dropdown do
    # frontend já sempre envia um valor real (gpt-4o/gpt-4o-mini/
    # gpt-4-turbo); este fallback só cobre uma chamada direta à API sem
    # passar por aquele formulário.
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name or "gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},  # Força json nativo se o modelo suportar
    )
    return _strip_markdown_json_fence(response.choices[0].message.content.strip())


def _call_anthropic(prompt: str, api_key: str, model_name: str, base_url: str = None) -> str:
    import anthropic

    model_name = _require_model(model_name, "Anthropic (Claude)")
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model_name,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise ValueError("O modelo Claude recusou processar este conteúdo.")
    text_parts = [block.text for block in response.content if block.type == "text"]
    return _strip_markdown_json_fence("".join(text_parts))


def _call_openai_compatible(prompt: str, api_key: str, model_name: str, base_url: str = None) -> str:
    """
    Qualquer provedor que fale a mesma API de chat completions da OpenAI
    (Groq, Mistral, DeepSeek, Together AI, OpenRouter, um Ollama local,
    etc.) — sem precisar de integração dedicada por provedor, desde que o
    usuário informe a URL base, o modelo e (se exigido) a chave.
    """
    from openai import OpenAI

    model_name = _require_model(model_name, "provedor compatível com OpenAI")
    if not base_url or not base_url.strip():
        raise ValueError(
            "Informe a URL base do provedor compatível com OpenAI nas Configurações "
            "(ex.: https://api.groq.com/openai/v1)."
        )
    # Alguns servidores locais (ex.: Ollama) não exigem chave real, mas o
    # SDK da OpenAI exige uma string não vazia.
    client = OpenAI(api_key=(api_key or "not-needed"), base_url=base_url.strip())
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )
    return _strip_markdown_json_fence(response.choices[0].message.content.strip())


# Registro de provedores: adicionar um novo provedor é só escrever uma
# função `_call_<provider>(prompt, api_key, model_name, base_url=None) -> str`
# (retornando o texto bruto da resposta, sem parsear o JSON ainda) e somar
# uma entrada aqui.
PROVIDERS = {
    "openai": _call_openai,
    "gemini": _call_gemini,
    "anthropic": _call_anthropic,
    "openai_compatible": _call_openai_compatible,
}


def parse_with_llm(
    file_path: str,
    provider: str,
    api_key: str,
    model_name: str = None,
    base_url: str = None,
) -> dict:
    """
    Extrai o conteúdo bruto de um arquivo (PDF ou doc antigo) e o roteia
    para um LLM de terceiros formatar as hierarquias e layouts de forma inteligente.
    """
    import fitz  # PyMuPDF

    # 1. Extração bruta ultrarrápida do conteúdo para mandar pro prompt
    doc = fitz.open(file_path)
    try:
        raw_text = chr(12).join([page.get_text() for page in doc])
        pages_read = len(doc)
    finally:
        doc.close()

    # Limitamos para evitar estourar contextos excessivamente, embora alguns modelos suportem 1M+.
    content_sample = raw_text[:30000]

    prompt = (
        "Analise o texto estrutural a seguir extraído de um documento corporativo/governamental. "
        "Formate este texto de volta em um array JSON estrito, identificando hierarquicamente os títulos (H1, H2), "
        "parágrafos e formatando possíveis tabelas como objetos aninhados. "
        "O output deve ser *estritamente* um JSON e nada mais.\n\n"
        f"Texto:\n{content_sample}"
    )

    provider_key = (provider or "").strip().lower()
    handler = PROVIDERS.get(provider_key)
    if handler is None:
        raise ValueError(
            f"Provedor de LLM desconhecido: '{provider}'. "
            f"Provedores suportados: {', '.join(sorted(PROVIDERS))}."
        )

    try:
        raw_response = handler(prompt, api_key, model_name, base_url)
        llm_extracted_json = json.loads(raw_response)
    except Exception as e:
        raise ValueError(f"Erro ao processar com provedor {provider}: {str(e)}")

    return format_json_output(
        {"source_type": f"pdf_llm_structured_{provider_key}", "pages_read": pages_read},
        [llm_extracted_json],
    )
