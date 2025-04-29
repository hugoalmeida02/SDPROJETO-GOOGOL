import requests

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = "AQUI_O_TEU_TOKEN_OPENAI"  # ⚠️ Substituir pelo teu Token

def get_openai_summary(terms):
    """Gera uma resposta/resumo usando o modelo GPT."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Responde de forma breve e objetiva."},
            {"role": "user", "content": f"Faz uma análise breve dos seguintes termos de pesquisa: {terms}"}
        ]
    }
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Erro ao consultar OpenAI: {e}")
        return "Não foi possível gerar a análise."