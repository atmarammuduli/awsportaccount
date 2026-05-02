from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class SNSHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "sns"

    @property
    def resource_type(self) -> str:
        return "Topic"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("sns")
        topics = client.list_topics()["Topics"]
        for topic in topics:
            topic["Name"] = topic["TopicArn"].split(":")[-1]
        return topics

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("sns")

        response = target_client.create_topic(Name=resource["Name"])
        return response["TopicArn"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("sns")
        try:
            target_client.get_topic_attributes(TopicArn=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["TopicArn"]

    def get_name(self, resource: dict) -> str:
        return resource["Name"]
