from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler
from rich.prompt import Confirm

class VPCHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "VPC"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        paginator = client.get_paginator("describe_vpcs")
        vpcs = []
        for page in paginator.paginate():
            vpcs.extend(page["Vpcs"])
        return vpcs

    def get_dependencies(self, resource: dict) -> List[tuple]:
        return [] # VPCs usually don't depend on other high-level resources we port

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")

        # Check if identical VPC exists (by Name tag)
        name = self.get_name(resource)
        existing = self._find_existing_by_name(target_client, name)

        if existing:
            if overwrite or Confirm.ask(f"VPC [bold]{name}[/bold] already exists. Delete and recreate? (Note: will fail if VPC is not empty)"):
                # Handle dependencies before deleting
                try:
                    target_client.delete_vpc(VpcId=existing["VpcId"])
                except Exception as e:
                    print(f"  [red]Error deleting VPC: {e}. Please empty the VPC manually or choose a different name.[/red]")
                    return existing["VpcId"]
            else:
                return existing["VpcId"]

        response = target_client.create_vpc(
            CidrBlock=resource["CidrBlock"],
            InstanceTenancy=resource["InstanceTenancy"]
        )
        vpc_id = response["Vpc"]["VpcId"]

        # Copy tags
        if "Tags" in resource:
            target_client.create_tags(Resources=[vpc_id], Tags=resource["Tags"])

        return vpc_id

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_vpcs(VpcIds=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["VpcId"]

    def get_name(self, resource: dict) -> str:
        for tag in resource.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return "unnamed-vpc"

    def _find_existing_by_name(self, client, name: str):
        if not name: return None
        vpcs = client.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": [name]}])["Vpcs"]
        return vpcs[0] if vpcs else None
