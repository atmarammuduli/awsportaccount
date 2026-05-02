from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class SQSHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "sqs"

    @property
    def resource_type(self) -> str:
        return "Queue"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("sqs")
        urls = client.list_queues().get("QueueUrls", [])
        return [{"QueueUrl": url, "Name": url.split("/")[-1]} for url in urls]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        source_client = self.session_manager.get_source_client("sqs")
        target_client = self.session_manager.get_target_client("sqs")

        attributes = source_client.get_queue_attributes(QueueUrl=resource["QueueUrl"], AttributeNames=["All"])["Attributes"]

        # Remove some attributes that shouldn't be passed to create_queue
        for attr in ["QueueArn", "CreatedTimestamp", "LastModifiedTimestamp"]:
            attributes.pop(attr, None)

        response = target_client.create_queue(
            QueueName=resource["Name"],
            Attributes=attributes
        )
        return response["QueueUrl"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("sqs")
        try:
            target_client.get_queue_attributes(QueueUrl=target_id, AttributeNames=["QueueArn"])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["QueueUrl"]

    def get_name(self, resource: dict) -> str:
        return resource["Name"]
