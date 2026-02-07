from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

class ChatCompletions:
    """
    A helper to call the OpenAI chat completions endpoint. 
    """
    def __init__(self, api_endpoint, engine_text, engine_visual=None):
        self.engine_text = engine_text
        # assign engine_visual to self.engine_visual if not null, otherwise engine_text
        self.engine_visual = engine_text if engine_visual is None else engine_visual
        
        token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

        self.client = AsyncAzureOpenAI(
            azure_endpoint=api_endpoint,
            api_version = "2023-12-01-preview",
            azure_ad_token_provider=token_provider)


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
    
    async def extract_keywords(self, query: str, max_tokens: int = 50):
        """
        Extract relevant search keywords from a user query.
        """
        prompt = f"Extract 3-5 relevant search keywords from this query that would be useful for finding documents in SharePoint. Return only the keywords separated by spaces, no explanations or formatting. Query: {query}"
        
        response = await self.client.chat.completions.create(
            model=self.engine_text,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts search keywords from user queries. Return only the keywords separated by spaces."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()