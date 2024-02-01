from openai import AsyncAzureOpenAI

class Embeddings:
    """
    Calculates embeddings for a given text using the Azure OpenAI embeddings endpoint.
    """
    def __init__(self, api_endpoint, api_key, engine):
        self.engine = engine
        self.client = AsyncAzureOpenAI(
            azure_endpoint=api_endpoint,
            api_key = api_key,
            api_version = "2023-05-15")

    async def get_embedding(self, text: str | list[str]):
        """
        TODO: introduce retries and throttling for long requests (documents of many fragments)
        """
        response = await self.client.embeddings.create(input=text, model=self.engine)
        return list(map(lambda x: x.embedding, response.data))


