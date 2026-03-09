from services.ai_service import groqclient
import asyncio

async def gk_agent(prompt: str):

    client = await groqclient.get_client()

    response = await client.chat.completions.create(
        model = "openai/gpt-oss-120b",
        messages = [{"role":"user","content":prompt}
                    ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    async def call():
        answer = await gk_agent("Which is the tallest mountain and deepest point on earth ?")
        print(answer)
    
    asyncio.run(call())