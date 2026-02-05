from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration, 
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

    client = SearchIndexClient(indexer_endpoint, DefaultAzureCredential())
    
    indexFound = False
    
    try:
        index = client.get_index(index_name)
        indexFound = True
    except Exception as e:
        print(f"Error getting index: {e}")
    pass

    if not indexFound:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=False, filterable=False, retrievable=True, searchable=False, facetable=False),  
            SimpleField(name="driveId", type=SearchFieldDataType.String, retrievable=True, filterable=False, searchable=False, facetable=False, sortable=False),  
            SimpleField(name="driveItemId", type=SearchFieldDataType.String, retrievable=True, filterable=False, searchable=False, facetable=False, sortable=False),  
            SimpleField(name="documentId", type=SearchFieldDataType.String, filterable=True, searchable=True, facetable=False, sortable=False, retrievable=True),  
            SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1536, vector_search_profile_name="vector-config-01", filterable=False, sortable=False, facetable=False),
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
                    name="vector-config-01", 
                    algorithm_configuration_name="alg-hnsw-01",
                    vectorizer_name="openai-vectorizer-01")
                ],
            algorithms=[        
                HnswAlgorithmConfiguration(  
                    name="alg-hnsw-01",
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
                    name="openai-vectorizer-01",
                    vectorizer_name="openai-vectorizer-01",
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=openai_endpoint,
                        deployment_name=embeddings_model,
                        model_name=embeddings_model
                    )
                )]
        )
        
        index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
        client.create_index(index)
        print("Index created")
    else:
        print("Index already exists")


    

        