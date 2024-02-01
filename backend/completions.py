from openai import AsyncAzureOpenAI

class ChatCompletions:
    """
    A helper to call the OpenAI chat completions endpoint. 
    """
    def __init__(self, api_endpoint, api_key, engine_text, engine_visual=None):
        self.engine_text = engine_text
        # assign engine_visual to self.engine_visual if not null, otherwise engine_text
        self.engine_visual = engine_text if engine_visual is None else engine_visual

        self.client = AsyncAzureOpenAI(
            azure_endpoint=api_endpoint,
            api_key = api_key,
            api_version = "2023-12-01-preview")


    async def generate(self, prompt: str, text: str, image_url: str = None, max_tokens: int = 300):
        content = [ {"type": "text", "text": text} ]
        if not image_url is None:
            content.append({ "type": "image_url", "image_url": { "url": image_url } })
            engine_to_use = self.engine_visual
        else:
            engine_to_use = self.engine_text 

        response = await self.client.chat.completions.create(
            model=engine_to_use,
            messages=[
                {
                "role": "user",
                "content": content,
                },
                {
                "role": "user",
                "content": [ {"type": "text", "text": prompt} ],
                },                
            ],
            max_tokens=max_tokens,
            )
        return response.choices[0].message.content