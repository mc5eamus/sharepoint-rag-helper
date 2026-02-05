import asyncio
import os
from auth import CallContext
from pdfprocessor import PdfProcessor
from docxprocessor import DocxProcessor
from embeddings import Embeddings
from indexer import Indexer
from drive import DriveFileFetcher
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from msal import ConfidentialClientApplication
from dateutil import parser
from search import SharePointIndex
from filestorage import FileStorage
from notificationhub import NotificationHub, NotificationChannel
from telemetry import get_logger

class SharePointRagOrchestrator:
    def __init__(self, app: ConfidentialClientApplication):
        self.app = app

        self.sp_index = SharePointIndex(app)

        self.embeddings = Embeddings(
            os.getenv("OPENAI_ENDPOINT"),
            os.getenv("OPENAI_EMBEDDINGS_MODEL"))

        self.indexer = Indexer(
            os.getenv("INDEXER_ENDPOINT"),
            os.getenv("INDEXER_INDEX"),
            self.embeddings,
            DefaultAzureCredential() )

        self.storage = FileStorage( 
            storage_account_name=os.getenv("BLOB_STORAGE_ACCOUNT_NAME"),
            container_name=os.getenv("BLOB_CONTAINER_NAME"))

        self.drive = DriveFileFetcher( app )

        self.notification_hub = NotificationHub(os.getenv("WEBPUBSUB_CONNECTION_STRING"), 'hub')

        self.log = get_logger()
    async def ensure_document_in_index(self, search_object: dict, ctx: CallContext):
        intercom = NotificationChannel(self.notification_hub, ctx)
        try:
            doc_id = await self.__ensure_document_in_index(search_object, ctx, intercom)
            intercom.send(f"Document {doc_id} has been indexed.")
            return doc_id
        except Exception as e:

            return ""
    
    async def search(self, keywords: str, query: str, ctx: CallContext, max_results: int = 3):
        
        self.log.info(f"Searching for '{keywords}' / '{query}'...")

        intercom = NotificationChannel(self.notification_hub, ctx)
        
        intercom.send(f"Asking sharepoint for '{keywords}'...")
        
        self.log.info(f"Asking sharepoint for '{keywords}'...")
        result = self.sp_index.search(keywords, ctx, max_results)

        self.log.info(f"Sharepoint returned {len(result)} results.")

        document_ids = []
        for r in result:
            self.log.info(f"Processing search result: {r['title']} ({r['id']})")
            safe_id = await self.__ensure_document_in_index(r, ctx, intercom)
            self.log.info(f"Document ensured in index: {safe_id}") 
            document_ids.append(safe_id)

        suggestions = list(self.indexer.get_from_index(query=query, ids=document_ids, k=max_results))
               
        intercom.send(f"Found {len(suggestions)} indexed fragments.")

        return suggestions
    
    
    async def search_indexed(self, query: str, ctx: CallContext, max_results: int = 3):
        
        self.log.info(f"Searching indexed documents for '{query}'...")

        intercom = NotificationChannel(self.notification_hub, ctx)
        intercom.send("Searching indexed documents...")
        
        try:
            suggestions = await self.__get_suggestions_from_index(query=query, ctx=ctx, max_results=max_results)
            
            intercom.send(f"Found {len(suggestions)} indexed fragments.")
            
            return suggestions
        except Exception as e:
            log.exception(e)
            intercom.send(f"Oops, something went wrong: {e}")
            return []

    async def __get_suggestions_from_index(self, query: str, ctx: CallContext, max_results: int = 3):
        
        # get more than we need so we can filter out inaccessible documents
        suggestions = self.indexer.get_from_index(query=query, k=max_results*10)
        
        # extract unique document ids
        document_ids = {}
        for s in suggestions:
            if s["documentId"] not in document_ids:
                document_ids[s["documentId"]] = [s['driveId'], s['driveItemId']]
        
        valid_suggestions = []
        accessible_documents = {}
        for s in suggestions:
            if s["documentId"] not in accessible_documents:
                try:
                    self.drive.get_item(s['driveId'], s['driveItemId'], ctx)
                    accessible_documents[s["documentId"]] = True
                except Exception as e:
                    # user does not have access to this document
                    accessible_documents[s["documentId"]] = False
            
            if accessible_documents[s["documentId"]]:
                valid_suggestions.append(s)
            
            if len(valid_suggestions) == max_results:
                break

        return valid_suggestions
            

    async def __ensure_document_in_index(self, search_object: dict, ctx: CallContext, intercom:NotificationChannel):

        self.log.info(f"Ensuring document is in index: {search_object['title']} ({search_object['id']})")     
        safe_id = Indexer.safe_id(search_object["driveId"], search_object["id"])
        last_modified = parser.parse(search_object["lastModified"])
        
        if not self.indexer.is_in_index(safe_id, last_modified):
            doctitle = search_object["title"]
            
            
            intercom.send(f"Found '{doctitle}' which is not in the index yet. Please bear with me, I'm indexing it...")
            
            print(f"Indexing {safe_id}")
            # get item from drive
            item = self.drive.get_item(search_object["driveId"], search_object["id"], ctx)

            filename = search_object["name"]
            filename_extension = os.path.splitext(filename)[1].lower()

            processor = None
            if filename_extension == ".docx":
                processor = DocxProcessor(item["downloadUrl"], 500)
            else:
                processor = PdfProcessor(item["downloadUrl"], self.storage)

            if processor is None:
                raise Exception(f"Unsupported file type: {filename_extension}")
            
            fragments = list(processor.split(safe_id))

            await self.indexer.index_with_embeddings( 
                docid=safe_id,
                driveId=search_object["driveId"],
                driveItemId=search_object["id"],
                uri=item["url"],
                title=doctitle,
                fragments=fragments)

            intercom.send(f"Making sure '{doctitle}' has been successfully indexed...")

            circuit_idx = 1
            while not self.indexer.is_in_index(safe_id):
                print(f"Waiting for indexing to complete: {circuit_idx}")
                await asyncio.sleep(1 + circuit_idx*2)
                circuit_idx += 1
                if circuit_idx > 5:
                    raise Exception("Indexing timeout")

        return safe_id