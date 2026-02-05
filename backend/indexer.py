import datetime
import re
from dateutil import parser
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from embeddings import Embeddings
from model import DocumentFragment

from azure.search.documents.models import VectorizableTextQuery

class IndexedItem:
    id: str
    score: float
    content: str
    uri: str
    title: str
    documentId: str
    driveId: str
    driveItemId: str
    imageUrl: str

class Indexer:
    """
    Indexer is a wrapper around Azure Cognitive Search. It takes care of indexing documents
    as well as performing search queries against the index.
    """
    def __init__(self, indexer_endpoint, index_name, emb: Embeddings, credential: AzureKeyCredential | DefaultAzureCredential = None):
        self.emb = emb
        self.credentials = credential
        self.indexer_endpoint = indexer_endpoint
        self.index_name = index_name

        if credential is None:
            self.credential = DefaultAzureCredential()
        else:
            self.credential = credential
        
        self.search_client = SearchClient(
            indexer_endpoint, 
            index_name, 
            self.credential)
        
    @staticmethod
    def safe_id(namespace, id):
        """
        Makes the id safe for use in the index as a document key.
        """
        return re.sub(r'[^a-zA-Z0-9_=-]', '_', f"{namespace}-{id}")

    async def index_with_embeddings(self, docid: str, driveId: str, driveItemId: str, uri: str, title: str, fragments: list[DocumentFragment]):
        """
        Submits the given fragments to the indexer. Fragments with less than 50 characters are ignored.
        """
        filtered_fragments = list(filter(lambda f: len(f.text) > 50, fragments))
        fragment_texts = [f.text for f in filtered_fragments]
        vectors = await self.emb.get_embedding(fragment_texts)
        documents = [{
            'id': f"{docid}-{i}",
            'chunk': i,
            'documentId': docid,
            'driveId': driveId,
            'driveItemId': driveItemId,
            'content': fragment.text, 
            'embedding': vectors[i],
            'uri': uri,
            'title': title,
            'lastModified': datetime.datetime.now(),
            'snapshot': fragment.snapshot
        } for i,fragment in enumerate(filtered_fragments)] 
        self.search_client.upload_documents(documents)
        

    def is_in_index(self, id: str, file_last_modified: datetime = None):
        """
        Verifies if the given id is in the index. If file_last_modified is given, it is used to check if the index is up to date.
        """
        print("Checking if document is in index:", id)

        results = list(self.search_client.search(
            search_text="*",
            filter="documentId eq '" + id + "'",
            select="lastModified",
            top=1))
        
        if(len(results) == 0):
            return False

        if (file_last_modified is None):
            return True

        lastModified = parser.isoparse(results[0]["lastModified"])

        return lastModified >= file_last_modified

    def get_from_index(self, query: str, ids: [str] = None, k: int = 1):
        """
        Executes a search query against the index. If ids is given, the query is restricted to the given ids.
        """
        q = VectorizableTextQuery(
            text=query,
            fields="embedding",
            k=k)
        
        if ids is None:
            filter = None
        elif len(ids) == 1:
            filter = "documentId eq '" + ids[0] + "'"
        else:
            filter = "search.in(documentId, '" + ",".join(ids) + "', ',')"

        res = list(self.search_client.search(
            search_text=query,
            filter=filter,
            select="id, content, uri, title, documentId, driveId, driveItemId, snapshot",
            vector_queries=[q],
            top=k))
        
        return [
            { 
                "id": h["id"], 
                "score": h["@search.score"],
                "content": h["content"],
                "uri": h["uri"],
                "title": h["title"],
                "documentId": h["documentId"],
                "driveId": h["driveId"],
                "driveItemId": h["driveItemId"],
                "snapshot": h["snapshot"]
            }
            for i,h in enumerate(res)]
    
