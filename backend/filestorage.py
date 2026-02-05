from datetime import datetime, timedelta, timezone
from azure.storage.blob import ContainerClient, BlobSasPermissions, generate_blob_sas, BlobServiceClient, UserDelegationKey
from azure.identity import DefaultAzureCredential

class FileStorage:
    """
    FileStorage is a wrapper around azure blob storage to keep snashots of document fragments.
    """    
    def __init__(self, 
                 container_name: str,
                 storage_connection_string: str = None, 
                 storage_account_name: str = None) -> None:
        
        print("Storage account name:", storage_account_name)
        print("Storage connection string:", storage_connection_string)
        print("Container name:", container_name)     

        if storage_connection_string is not None:
            self.container_client = ContainerClient.from_connection_string(storage_connection_string, container_name)
            self.blob_service_client = None
        elif storage_account_name is not None:
            self.credential = DefaultAzureCredential()
            self.storage_account_name = storage_account_name
            container_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}"
            self.container_client = ContainerClient.from_container_url(container_url, credential=self.credential)
            # Create BlobServiceClient for user delegation key
            service_url = f"https://{storage_account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url=service_url, credential=self.credential)
        else:
            raise ValueError("Either storage_connection_string or storage_account_name must be provided")

    def put(self, file: bytes, filename: str):
        blob_client = self.container_client.get_blob_client(filename)
        blob_client.upload_blob(file, overwrite=True)

    
    def get_link(self, filename: str) -> str:
        blob_client = self.container_client.get_blob_client(filename)
        
        # If using connection string (account key), use the original method
        if self.blob_service_client is None:
            # generate sas token for blob using account key
            sas_token = generate_blob_sas(
                account_name=self.container_client.account_name,
                container_name=self.container_client.container_name,
                blob_name=blob_client.blob_name,
                account_key=self.container_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry= datetime.now(timezone.utc) + timedelta(hours=1)
            )
        else:
            # Use user delegation SAS with managed identity
            # Get user delegation key
            key_start_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            key_expiry_time = key_start_time + timedelta(hours=1)
            
            user_delegation_key = self.blob_service_client.get_user_delegation_key(
                key_start_time=key_start_time,
                key_expiry_time=key_expiry_time
            )
            
            sas_token = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=self.container_client.container_name,
                blob_name=blob_client.blob_name,
                user_delegation_key=user_delegation_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=1)
            )
        
        # build the url
        return f"{blob_client.url}?{sas_token}"

