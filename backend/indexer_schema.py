from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIParameters,  
    AzureOpenAIVectorizer,
    HnswVectorSearchAlgorithmConfiguration, 
    HnswParameters,
    SearchFieldDataType,
    SearchIndex,
    SearchField,
    SimpleField,
    VectorSearch, 
    VectorSearchProfile, 
    VectorSearchAlgorithmKind, 
    VectorSearchAlgorithmMetric
)

def ensure_index_exists(indexer_endpoint, index_name, mgmt_key, openai_endpoint, openai_key, embeddings_model):
    """
    Creates the index if it doesn't exist
    """

    client = SearchIndexClient(indexer_endpoint, AzureKeyCredential(mgmt_key))
    
    indexFound = False
    
    try:
        index = client.get_index(index_name)
        indexFound = True
    except:
        pass

    if not indexFound:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=False, filterable=False, retrievable=True, searchable=False, facetable=False),  
            SimpleField(name="driveId", type=SearchFieldDataType.String, retrievable=True, filterable=False, searchable=False, facetable=False, sortable=False),  
            SimpleField(name="driveItemId", type=SearchFieldDataType.String, retrievable=True, filterable=False, searchable=False, facetable=False, sortable=False),  
            SimpleField(name="documentId", type=SearchFieldDataType.String, filterable=True, searchable=True, facetable=False, sortable=False, retrievable=True),  
            SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1536, vector_search_profile="vector-config", filterable=False, sortable=False, facetable=False),
            SimpleField(name="uri", type=SearchFieldDataType.String, analyzer_name="standard.lucene", retrievable=True, searchable=False, filterable=False, sortable=False, facetable=False),  
            SearchField(name="title", type=SearchFieldDataType.String, filterable=False, sortable=False, facetable=False),  
            SimpleField(name="chunk", type=SearchFieldDataType.Int32, sortable=True, filterable=False, retrievable=True, searchable=False, facetable=False),  
            SearchField(name="content", type=SearchFieldDataType.String, analyzer_name="standard.lucene", filterable=False, sortable=False, facetable=False),
            SimpleField(name="lastModified", type=SearchFieldDataType.DateTimeOffset, retrievable=True, searchable=False, filterable=False, sortable=False, facetable=False),
            SimpleField(name="snapshot", type=SearchFieldDataType.String, retrievable=True, searchable=False, filterable=False, sortable=False, facetable=False)
        ]  

        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="vector-config", 
                    algorithm="alg-hnsw",
                    vectorizer="openai-vectorizer")
                ],
            algorithms=[        
                HnswVectorSearchAlgorithmConfiguration(  
                    name="alg-hnsw",
                    kind=VectorSearchAlgorithmKind.HNSW,  
                    parameters=HnswParameters(  
                        m=4,  
                        ef_construction=400,  
                        ef_search=500,  
                        metric=VectorSearchAlgorithmMetric.COSINE,  
                    ),  
                ),
            ],
            vectorizers=[
                AzureOpenAIVectorizer(  
                    name="openai-vectorizer",  
                    kind="azureOpenAI",  
                    azure_open_ai_parameters=AzureOpenAIParameters(  
                        resource_uri=openai_endpoint,  
                        deployment_id=embeddings_model,  
                        api_key=openai_key,  
                    ),  
                )]
        )
        
        index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
        client.create_index(index)
        print("Index created")
    else:
        print("Index already exists")


    

        