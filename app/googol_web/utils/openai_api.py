import openai
from fastapi import HTTPException
import os

# Definir a chave da API da OpenAI (pode ser armazenada em variáveis de ambiente)
# openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = "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"

async def generate_analysis(search_terms: str):
    # Formatar a consulta para enviar à OpenAI
    prompt = f"Faça uma análise sobre os seguintes termos de pesquisa: {search_terms}. "
    prompt += "Forneça uma análise contextualizada sobre os termos."

    try:
        # Chamada à API da OpenAI para gerar uma resposta contextualizada
        response = openai.Completion.create(
            engine="gpt-4o",  # Ou outro modelo da OpenAI (ex: gpt-3.5-turbo)
            prompt=prompt,
            max_tokens=500,
            temperature=0.7  # Controla a criatividade da resposta
        )
        return response.choices[0].text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))