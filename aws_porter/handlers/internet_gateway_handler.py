from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class InternetGatewayHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "InternetGateway"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        return client.describe_internet_gateways()["InternetGateways"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        # IGs are attached to VPCs, but created independently
        deps = []
        for attachment in resource.get("Attachments", []):
            if attachment.get("VpcId"):
                deps.append(("ec2", "VPC", attachment["VpcId"]))
        return deps

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")

        response = target_client.create_internet_gateway()
        igw_id = response["InternetGateway"]["InternetGatewayId"]

        if "Tags" in resource:
            target_client.create_tags(Resources=[igw_id], Tags=resource["Tags"])

        # Attach to VPC if necessary
        for attachment in resource.get("Attachments", []):
            source_vpc_id = attachment.get("VpcId")
            if source_vpc_id:
                target_vpc_id = self.registry.get_target_id("ec2", "VPC", source_vpc_id)
                if target_vpc_id:
                    target_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=target_vpc_id)

        return igw_id

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_internet_gateways(InternetGatewayIds=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["InternetGatewayId"]

    def get_name(self, resource: dict) -> str:
        for tag in resource.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return "unnamed-igw"
