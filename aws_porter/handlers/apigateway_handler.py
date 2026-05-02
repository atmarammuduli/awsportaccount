from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class APIGatewayHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "apigateway"

    @property
    def resource_type(self) -> str:
        return "RestApi"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("apigateway")
        paginator = client.get_paginator("get_rest_apis")
        apis = []
        for page in paginator.paginate():
            apis.extend(page.get("items", []))
        return apis

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        source_client = self.session_manager.get_source_client("apigateway")
        target_client = self.session_manager.get_target_client("apigateway")

        api_id = resource["id"]

        # Find a stage to export from
        stages = source_client.get_stages(restApiId=api_id).get("item", [])
        if not stages:
             raise Exception(f"No stages found for API {api_id}, cannot export.")
        stage_name = stages[0]["stageName"]

        # Best way to port API Gateway is using Export/Import (OpenAPI)
        export = source_client.get_export(
            restApiId=api_id,
            stageName=stage_name,
            exportType="oas30",
            parameters={"extensions": "integrations"}
        )
        body = export["body"].read()

        response = target_client.import_rest_api(
            body=body,
            failOnWarnings=False
        )
        return response["id"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("apigateway")
        try:
            target_client.get_rest_api(restApiId=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["id"]

    def get_name(self, resource: dict) -> str:
        return resource["name"]
