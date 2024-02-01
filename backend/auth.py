import base64
from dataclasses import dataclass
import json
from msal import ConfidentialClientApplication

SCOPES = ["https://graph.microsoft.com/.default"]

@dataclass
class CallContext:
    """
    Keeps the token to be reused for subsequent calls.
    """
    token: str # access token to call the downstream API (Graph)
    user_token: str # token of the user on behalf of whom we're calling

    @staticmethod
    def for_app(app: ConfidentialClientApplication):
        return CallContext(get_app_token(app), None)
    
    @staticmethod
    def for_user(user_token: str):
        return CallContext(None, user_token)
    
def get_user_id(token: str): 
    """
    Returns the user id from the token.
    """

    user_json = json.loads(base64.b64decode(token.split(".")[1] + '=='))
    user_id = user_json['oid']
    return user_id
    
def get_token(app: ConfidentialClientApplication, ctx: CallContext = None):
    """
    Obtains the token for the downstream API or reuses the existing one.
    """
    
    if ctx.token:
        return ctx.token
    
    if ctx.user_token:
        token = app.acquire_token_on_behalf_of(ctx.user_token, SCOPES)
    
    ctx.token = token["access_token"]
    
    return token["access_token"]

def get_app_token(app: ConfidentialClientApplication):
    """
    Retrieves an token for the app using the client credentials flow.
    """
    token = app.acquire_token_for_client(scopes=SCOPES)
    return token["access_token"]
