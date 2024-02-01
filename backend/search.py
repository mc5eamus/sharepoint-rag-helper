from msal import ConfidentialClientApplication
import requests
from auth import CallContext, get_token

class SharePointIndex:
    def __init__(self, app: ConfidentialClientApplication):
        self.app = app

    def search(self, query: str, ctx: CallContext, max_results: int = 3) -> [dict]:
        token = get_token(self.app, ctx)
        url = f"https://graph.microsoft.com/v1.0/search/query"
        headers = {"Authorization": "Bearer " + token}
        body = {
            "requests": [
                {
                    "entityTypes": [
                        "listItem", "driveItem"
                    ],
                    "query": {
                        "queryString": f"{query} AND isDocument=true AND (filetype:pdf OR filetype:docx)"
                    },
                    "fields": [
                        "id",
                        "parentReference",
                        "name",
                        "title",
                        "driveId",
                        "lastModifiedDateTime"
                    ],
                    "size": max_results,
                    #"region": "EMEA"
                }
            ]
        }
        response = requests.post(url, headers=headers, json=body)
        if response.status_code >= 200 and response.status_code < 300:
            payload = response.json()

            # payload example in search_result.json
            # extract individual hits
            
            if len(payload["value"][0]["hitsContainers"]) == 0 or "hits" not in payload["value"][0]["hitsContainers"][0]:
                return []

            hits = payload["value"][0]["hitsContainers"][0]["hits"]
            return [
                {   "id": h["resource"]["id"],
                    "name": h["resource"]["name"],
                    "title": h["resource"]["listItem"]["fields"]["title"],
                    "lastModified": h["resource"]["lastModifiedDateTime"],
                    "driveId": h["resource"]["parentReference"]["driveId"],
                    "summary": h["summary"],
                    "rank": h["rank"] }

                 for i,h in enumerate(hits)]
        else:
            raise Exception(response.status_code, response.text)
