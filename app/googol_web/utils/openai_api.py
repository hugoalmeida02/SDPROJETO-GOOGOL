from openai import OpenAI
from fastapi import HTTPException

from ..config import settings

# Cliente da API OpenAI com chave secreta
client = OpenAI(api_key=settings.openai_api_token)

# Gera uma análise textual com base nos termos da pesquisa
async def generate_analysis(search_terms: str):
    prompt = f"Baseando-te nos seguintes termos de pesquisa:  {search_terms}. "
    prompt += "Forneça uma análise contextualizada sobre os termos."

    try:
        response = client.responses.create(
            model="gpt-4o",
            input=prompt
        )
        
        return response.output_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

