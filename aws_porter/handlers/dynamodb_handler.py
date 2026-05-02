from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class DynamoDBHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "dynamodb"

    @property
    def resource_type(self) -> str:
        return "Table"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("dynamodb")
        paginator = client.get_paginator("list_tables")
        tables = []
        for page in paginator.paginate():
            for name in page["TableNames"]:
                tables.append({"TableName": name})
        return tables

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        source_client = self.session_manager.get_source_client("dynamodb")
        target_client = self.session_manager.get_target_client("dynamodb")

        table_name = resource["TableName"]
        desc = source_client.describe_table(TableName=table_name)["Table"]

        # Prepare creation args from description
        create_args = {
            "TableName": table_name,
            "AttributeDefinitions": desc["AttributeDefinitions"],
            "KeySchema": desc["KeySchema"]
        }

        if "BillingModeSummary" in desc:
            create_args["BillingMode"] = desc["BillingModeSummary"]["BillingMode"]

        if desc.get("ProvisionedThroughput", {}).get("ReadCapacityUnits"):
             if create_args.get("BillingMode") != "PAY_PER_REQUEST":
                create_args["ProvisionedThroughput"] = {
                    "ReadCapacityUnits": desc["ProvisionedThroughput"]["ReadCapacityUnits"],
                    "WriteCapacityUnits": desc["ProvisionedThroughput"]["WriteCapacityUnits"]
                }

        response = target_client.create_table(**create_args)
        return response["TableDescription"]["TableName"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("dynamodb")
        try:
            target_client.describe_table(TableName=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["TableName"]

    def get_name(self, resource: dict) -> str:
        return resource["TableName"]
