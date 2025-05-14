from openai import OpenAI
from fastapi import HTTPException


from ..config import settings

# Cliente da API OpenAI com chave secreta
client = OpenAI(api_key="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")

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

