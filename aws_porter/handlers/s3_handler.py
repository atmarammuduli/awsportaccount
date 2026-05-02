from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler
from rich.prompt import Prompt

class S3Handler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "s3"

    @property
    def resource_type(self) -> str:
        return "Bucket"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("s3")
        return client.list_buckets()["Buckets"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        source_client = self.session_manager.get_source_client("s3")
        target_client = self.session_manager.get_target_client("s3")
        source_bucket = resource["Name"]

        # Check if identical exists
        try:
            target_client.head_bucket(Bucket=source_bucket)
            exists = True
        except:
            exists = False

        target_account_id = self.session_manager.get_target_account_id()
        suggested_name = source_bucket if not exists else f"{source_bucket}-{target_account_id}"

        target_bucket = Prompt.ask(f"Enter target bucket name for [bold]{source_bucket}[/bold]", default=suggested_name)

        # Create bucket
        region = self.session_manager.target_region
        create_config = {}
        if region != "us-east-1":
            create_config = {"LocationConstraint": region}

        if create_config:
            target_client.create_bucket(Bucket=target_bucket, CreateBucketConfiguration=create_config)
        else:
            target_client.create_bucket(Bucket=target_bucket)

        # Port settings (Versioning, Encryption, Tags)
        try:
            tags = source_client.get_bucket_tagging(Bucket=source_bucket).get("TagSet", [])
            if tags:
                target_client.put_bucket_tagging(Bucket=target_bucket, Tagging={"TagSet": tags})
        except: pass

        try:
            versioning = source_client.get_bucket_versioning(Bucket=source_bucket).get("Status")
            if versioning:
                target_client.put_bucket_versioning(Bucket=target_bucket, VersioningConfiguration={"Status": versioning})
        except: pass

        return target_bucket

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("s3")
        try:
            target_client.head_bucket(Bucket=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["Name"]

    def get_name(self, resource: dict) -> str:
        return resource["Name"]
