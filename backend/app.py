import dotenv
import os
import logging
import uvicorn
from opentelemetry import trace

#from dapr.ext.fastapi import DaprApp
from msal import ConfidentialClientApplication
from azure.core.credentials import AzureKeyCredential
from fastapi import FastAPI, Depends, Response, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import Annotated, Optional
from pydantic import BaseModel

from orchestration import SharePointRagOrchestrator
from auth import CallContext, get_user_id
from filestorage import FileStorage
from notificationhub import NotificationChannel, NotificationHub
from completions import ChatCompletions
from telemetry import setup_telemetry, get_logger
from indexer_schema import ensure_index_exists


dotenv.load_dotenv()

setup_telemetry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_logger().info("Ensuring index exists...")
    ensure_index_exists(
        os.getenv("INDEXER_ENDPOINT"),
        os.getenv("INDEXER_INDEX"),
        os.getenv("INDEXER_MANAGE_KEY"),
        os.getenv("OPENAI_ENDPOINT"),
        os.getenv("OPENAI_APIKEY"),
        os.getenv("OPENAI_EMBEDDINGS_MODEL") )
    yield

app = FastAPI(lifespan=lifespan)


# adjust it to your needs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#dapr_app = DaprApp(app)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
tenant_id = os.getenv("TENANT_ID")
access_principal_delegated = ConfidentialClientApplication(
    os.getenv("CLIENT_ID"), 
    authority=f"https://login.microsoftonline.com/{tenant_id}", 
    client_credential=os.getenv("CLIENT_SECRET"))

orchestrator = SharePointRagOrchestrator(access_principal_delegated)

storage = FileStorage(
    storage_connection_string=os.getenv("BLOB_CONNECTION_STRING"), 
    container_name=os.getenv("BLOB_CONTAINER_NAME"))

notification_hub = NotificationHub(os.getenv("WEBPUBSUB_CONNECTION_STRING"), 'hub')

chat_completions = ChatCompletions(os.getenv("OPENAI_ENDPOINT"),
    os.getenv("OPENAI_APIKEY"),
    os.getenv("OPENAI_COMPLETIONS_MODEL_TEXT"), 
    os.getenv("OPENAI_COMPLETIONS_MODEL_VISUAL"))

class SearchRequestItem(BaseModel):
    """
    Search request from the frontend.
    keywords: keywords to search for in SharePoint
    query: query to search for in the index
    """
    keywords: str
    query: str
    max_results: Optional[int] = 3

class CompletionRequestItem(BaseModel):
    """
    For testing purposes only, we provide a way to validate the retrieved data
    and ask the question to either text or multimodal model. Here's how the request is shaped.
    """
    query: str
    text: str
    image: Optional[str] = None


class SharePointSearchResult(BaseModel):
    """
    Represents a search result from SharePoint via Microsoft Graph.
    It has the minimal set of attributes required to proceed with indexing.
    """
    documentId: str
    driveId: str
    driveItemId: str
    lastModified: str
    title: Optional[str] = None

@app.post("/api/suggestions")
async def suggestions_from_sharepoint(
    token: Annotated[str, Depends(oauth2_scheme)],
    item: SearchRequestItem):
    """
    Reach out to SharePoint to get documents as candidates.
    Make sure they are indexed.
    Execute a query against the index. 
    It doesn't guarantee that all the documents retrieved from SharePoint
    will be involved, it simply takes the best chungs from the index.
    """
    with trace.get_tracer(__name__).start_as_current_span("suggestions-full") as activity:
    
        ctx = CallContext.for_user(token)

        activity.add_event(f"Reaching out to SharePoint for '{item.keywords}'")

        return await orchestrator.search(item.keywords, item.query, ctx, item.max_results)

@app.post("/api/indexed")
async def suggestions_from_index(
    token: Annotated[str, Depends(oauth2_scheme)],
    item: SearchRequestItem):
    """
    Search for suggestions in the prepopulated index, 
    SharePoint will only be consulted for permissions.
    """
    with trace.get_tracer(__name__).start_as_current_span("suggestions-indexed") as activity:
        ctx = CallContext.for_user(token)

        activity.add_event(f"Looking for '{item.query}' in the index")
        return await orchestrator.search_indexed(item.query, ctx, item.max_results)

@app.get("/api/media/{filename}", response_class=RedirectResponse, status_code=302)
async def media_file(filename: str, response: Response):
    """
    Returns a redirect to a media file from the storage account.
    """
    try :
        return RedirectResponse(storage.get_link(filename))
    except:
        response.status_code = status.HTTP_404_NOT_FOUND
        return None
    
@app.get("/api/url/{filename}")
async def media_url(filename: str, response: Response):
    """
    Returns a URL to the media file including the SAS token.
    """        
    try :
        return storage.get_link(filename)
    except:
        response.status_code = status.HTTP_404_NOT_FOUND
        return None    
    
@app.post("/api/comms/negotiate")
async def get_notification_client_token(
    token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Obtains a token for the client to establish a connection 
    with the notification hub.
    """        
    return notification_hub.negotiate(get_user_id(token))

@app.post("/api/indexed/item")
async def ensure_index(
    token: Annotated[str, Depends(oauth2_scheme)],
    search_result: SharePointSearchResult):
    """
    Will likely be used in the nearest future in a distributed/parallel scenario 
    where we can delegate indexing to a separate process.
    """
    ctx = CallContext.for_user(token)
    docid = await orchestrator.ensure_index(search_result, ctx)
    return docid


@app.post("/api/completions/chat")
async def completions(
    token: Annotated[str, Depends(oauth2_scheme)],
    item: CompletionRequestItem):
    """
    A simple completion endpoint to test the model on a single fragment (text or visual).
    """

    ctx = CallContext.for_user(token)
    
    intercom = NotificationChannel(notification_hub, ctx)
        
    imageUrl = None
    if not item.image is None:
        imageUrl = storage.get_link(item.image)
        intercom_message  = "Asking a visual model for help, it may take a while..."
    else:
        intercom_message  = "Asking a model for help, should be back in a jiffy..."

    intercom.send(intercom_message)

    try:
        result = await chat_completions.generate(item.query, item.text, imageUrl)
        intercom.send(f"Here we go")

    except Exception as e:
        intercom.send(f"Oops, something went wrong: {e}")
        result = ""
    
    return result

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8085))
    host = os.getenv('HOST', "0.0.0.0")
    if os.getenv('DEBUG', 'false').lower() == 'true':
        uvicorn.run("app:app", host=host, port=port, reload=True)
    else:
        uvicorn.run(app, host=host, port=port)