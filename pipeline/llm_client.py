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
    """Send a message to Claude and get a text response.

    Args:
        system_prompt: Instructions that define Claude's behavior.
        messages: Conversation history as a list of {"role", "content"} dicts.
        model: Which Claude model to use. Defaults to Haiku (cheapest).
        temperature: 0 for deterministic, higher for more creative.
        max_tokens: Maximum length of response.

    Returns:
        The assistant's text response as a string.
    """
    
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

def chat_with_tools(
        system_prompt, 
        messages, 
        tools, 
        model="claude-haiku-4-5-20251001",
        temperature=0,
        max_tokens=1024
):
    """Send a message to Claude with tool definitions for structured output.

    When Claude has enough information, it "calls" a tool with structured data
    while also providing a conversational reply. This separates what the user
    sees (text) from what the code uses (structured profile).

    Args:
        system_prompt: Instructions that define Claude's behavior.
        messages: Conversation history as a list of {"role", "content"} dicts.
        tools: List of tool definitions (JSON schema format).
        model: Which Claude model to use. Defaults to Haiku (cheapest).
        temperature: 0 for deterministic, higher for more creative.
        max_tokens: Maximum length of response.

    Returns:
        Tuple of (text, tool_input):
            text: The conversational reply shown to the user.
            tool_input: Dict of extracted data if a tool was called, else None.
    """

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
        tools=tools,
    )
    text = ""
    tool_input = None

    for block in response.content:
        if block.type == "text":
            text = block.text
        elif block.type == "tool_use":
            tool_input = block.input
    return text, tool_input