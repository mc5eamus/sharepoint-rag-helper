from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

class Embeddings:
    """
    Calculates embeddings for a given text using the Azure OpenAI embeddings endpoint.
    """
    def __init__(self, api_endpoint, engine):
        self.engine = engine

        token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

        self.client = AsyncAzureOpenAI(
            azure_endpoint=api_endpoint,
            api_version = "2023-05-15",
            azure_ad_token_provider=token_provider)

    async def get_embedding(self, text: str | list[str]):
        """
        TODO: introduce retries and throttling for long requests (documents of many fragments)
        """
        response = await self.client.embeddings.create(input=text, model=self.engine)
        return list(map(lambda x: x.embedding, response.data))


