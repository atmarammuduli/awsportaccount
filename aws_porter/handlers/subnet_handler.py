from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class SubnetHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "Subnet"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        paginator = client.get_paginator("describe_subnets")
        subnets = []
        for page in paginator.paginate():
            subnets.extend(page["Subnets"])
        return subnets

    def get_dependencies(self, resource: dict) -> List[tuple]:
        return [("ec2", "VPC", resource["VpcId"])]

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")

        target_vpc_id = self.registry.get_target_id("ec2", "VPC", resource["VpcId"])
        if not target_vpc_id:
            raise Exception(f"Target VPC for source VPC {resource['VpcId']} not found in registry.")

        # Check for existing
        name = self.get_name(resource)
        existing = self._find_existing_by_name(target_client, target_vpc_id, name)
        if existing:
            return existing["SubnetId"]

        response = target_client.create_subnet(
            VpcId=target_vpc_id,
            CidrBlock=resource["CidrBlock"],
            AvailabilityZone=resource.get("AvailabilityZone")
        )
        subnet_id = response["Subnet"]["SubnetId"]

        if "Tags" in resource:
            target_client.create_tags(Resources=[subnet_id], Tags=resource["Tags"])

        return subnet_id

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_subnets(SubnetIds=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["SubnetId"]

    def get_name(self, resource: dict) -> str:
        for tag in resource.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return "unnamed-subnet"

    def _find_existing_by_name(self, client, vpc_id, name: str):
        if not name: return None
        subnets = client.describe_subnets(Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "tag:Name", "Values": [name]}
        ])["Subnets"]
        return subnets[0] if subnets else None
