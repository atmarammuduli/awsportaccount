from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class EventBridgeHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "events"

    @property
    def resource_type(self) -> str:
        return "Rule"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("events")
        paginator = client.get_paginator("list_rules")
        rules = []
        for page in paginator.paginate():
            rules.extend(page["Rules"])
        return rules

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("events")

        args = {
            "Name": resource["Name"],
            "ScheduleExpression": resource.get("ScheduleExpression"),
            "EventPattern": resource.get("EventPattern"),
            "State": resource["State"],
            "Description": resource.get("Description", ""),
        }
        # Filter out None values
        args = {k: v for k, v in args.items() if v is not None}

        response = target_client.put_rule(**args)
        return response["RuleArn"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("events")
        try:
            target_client.describe_rule(Name=target_id.split("/")[-1])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["Name"]

    def get_name(self, resource: dict) -> str:
        return resource["Name"]
