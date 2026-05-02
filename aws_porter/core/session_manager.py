import boto3
from typing import Optional

class SessionManager:
    def __init__(
        self,
        source_profile: Optional[str] = None,
        target_profile: Optional[str] = None,
        source_region: str = "us-east-1",
        target_region: Optional[str] = None,
        source_access_key: Optional[str] = None,
        source_secret_key: Optional[str] = None,
        target_access_key: Optional[str] = None,
        target_secret_key: Optional[str] = None,
    ):
        self.source_region = source_region
        self.target_region = target_region or source_region

        if source_access_key and source_secret_key:
            self.source_session = boto3.Session(
                aws_access_key_id=source_access_key,
                aws_secret_access_key=source_secret_key,
                region_name=self.source_region
            )
        else:
            self.source_session = boto3.Session(
                profile_name=source_profile,
                region_name=self.source_region
            )

        if target_access_key and target_secret_key:
            self.target_session = boto3.Session(
                aws_access_key_id=target_access_key,
                aws_secret_access_key=target_secret_key,
                region_name=self.target_region
            )
        else:
            self.target_session = boto3.Session(
                profile_name=target_profile,
                region_name=self.target_region
            )

    def get_source_client(self, service_name: str):
        return self.source_session.client(service_name)

    def get_target_client(self, service_name: str):
        return self.target_session.client(service_name)

    def get_source_account_id(self) -> str:
        return self.source_session.client("sts").get_caller_identity()["Account"]

    def get_target_account_id(self) -> str:
        return self.target_session.client("sts").get_caller_identity()["Account"]
