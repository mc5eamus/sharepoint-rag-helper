from datetime import datetime, timedelta
from azure.storage.blob import ContainerClient, BlobSasPermissions, generate_blob_sas

class FileStorage:
    """
    FileStorage is a wrapper around azure blob storage to keep snashots of document fragments.
    """
    def __init__(self, storage_connection_string: str, container_name: str) -> None:
        self.container_client = ContainerClient.from_connection_string(storage_connection_string, container_name)

    def put(self, file: bytes, filename: str):
        blob_client = self.container_client.get_blob_client(filename)
        blob_client.upload_blob(file, overwrite=True)

    
    def get_link(self, filename: str) -> str:
        blob_client = self.container_client.get_blob_client(filename)
        # generate sas token for blob
        sas_token = generate_blob_sas(
            account_name=self.container_client.account_name,
            container_name=self.container_client.container_name,
            blob_name=blob_client.blob_name,
            account_key=self.container_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry= datetime.utcnow() + timedelta(hours=1)
        )
        # build the url
        return f"{blob_client.url}?{sas_token}"

