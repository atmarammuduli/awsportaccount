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
        return client.get_rest_apis()["items"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        source_client = self.session_manager.get_source_client("apigateway")
        target_client = self.session_manager.get_target_client("apigateway")

        api_id = resource["id"]

        # Best way to port API Gateway is using Export/Import (OpenAPI)
        export = source_client.get_export(
            restApiId=api_id,
            stageName="prod", # Assumption
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
