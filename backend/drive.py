import requests
from msal import ConfidentialClientApplication
from auth import CallContext, get_token

class DriveFileFetcher:
    """
    Graph API helper for interacting with files on SharePoint/OneDrive
    """
    def __init__(self, app: ConfidentialClientApplication) -> None:
        self.app = app

    @staticmethod
    def item_url(driveid, itemid):
        return f"https://graph.microsoft.com/v1.0/drives/{driveid}/items/{itemid}"
    
    def __get_item_info(self, driveid, itemid, ctx: CallContext):
        """
        We're retrieving a temporary URL to fetch the file and some additional metadata.
        """
        url = DriveFileFetcher.item_url(driveid, itemid)
        token = get_token(self.app, ctx)
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code >= 200 and response.status_code < 300:
            payload = response.json()
            driveitem = { 
                'id': payload["id"],
                'name': payload["name"],
                'url': payload["webUrl"],
                'lastModified': payload["lastModifiedDateTime"],
                'downloadUrl': payload["@microsoft.graph.downloadUrl"] }
            return driveitem
        else:
            raise Exception(response.status_code, response.text)

    def get_item(self, driveid, itemid, ctx: CallContext) -> dict:
        try:
            item = self.__get_item_info(driveid, itemid, ctx)
            return item
        except:
            raise Exception("Unable to get item info")
