import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

def chat(
    system_prompt, 
    messages, 
    model="claude-haiku-4-5-20251001", 
    temperature=0, 
    max_tokens=1024
):
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
    )
    return response.content[0].text