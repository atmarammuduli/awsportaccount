from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class NATGatewayHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "NatGateway"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        return client.describe_nat_gateways()["NatGateways"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return [("ec2", "Subnet", resource["SubnetId"])]

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")
        target_subnet_id = self.registry.get_target_id("ec2", "Subnet", resource["SubnetId"])

        # NAT Gateway needs an Elastic IP. Let's allocate one.
        allocation = target_client.allocate_address(Domain="vpc")
        allocation_id = allocation["AllocationId"]

        response = target_client.create_nat_gateway(
            SubnetId=target_subnet_id,
            AllocationId=allocation_id
        )
        ngw_id = response["NatGateway"]["NatGatewayId"]

        if "Tags" in resource:
            target_client.create_tags(Resources=[ngw_id], Tags=resource["Tags"])

        return ngw_id

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_nat_gateways(NatGatewayIds=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["NatGatewayId"]

    def get_name(self, resource: dict) -> str:
        for tag in resource.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return "unnamed-nat-gw"
