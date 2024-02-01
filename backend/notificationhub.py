from auth import CallContext, get_user_id
from azure.messaging.webpubsubservice import WebPubSubServiceClient

class NotificationHub:
    def __init__(self, connection_string: str, hub: str) -> None:
        self.client = WebPubSubServiceClient.from_connection_string(connection_string, hub=hub)

    def negotiate(self, user_id: str):
        return self.client.get_client_access_token(user_id=user_id)

    def send(self, message: str, user: str = None):
        if(user == None):
            self.client.send_to_all(message)
        else:
            self.client.send_to_user(message, user)

class NotificationChannel: 
    def __init__(self, hub: NotificationHub, ctx: CallContext) -> None:
        self.hub = hub
        self.user_id = get_user_id(ctx.user_token)

    def send(self, message: str):
        self.hub.send(self.user_id, message)

