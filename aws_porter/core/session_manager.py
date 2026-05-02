import boto3
from typing import Optional

class SessionManager:
    def __init__(
        self,
        source_profile: str,
        target_profile: str,
        source_region: str,
        target_region: Optional[str] = None
    ):
        self.source_profile = source_profile
        self.target_profile = target_profile
        self.source_region = source_region
        self.target_region = target_region or source_region

        self.source_session = boto3.Session(
            profile_name=self.source_profile,
            region_name=self.source_region
        )
        self.target_session = boto3.Session(
            profile_name=self.target_profile,
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
