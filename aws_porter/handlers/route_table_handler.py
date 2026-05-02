from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class RouteTableHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "RouteTable"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        paginator = client.get_paginator("describe_route_tables")
        rts = []
        for page in paginator.paginate():
            rts.extend(page["RouteTables"])
        return rts

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return [("ec2", "VPC", resource["VpcId"])]

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")
        target_vpc_id = self.registry.get_target_id("ec2", "VPC", resource["VpcId"])

        # Create route table
        response = target_client.create_route_table(VpcId=target_vpc_id)
        rt_id = response["RouteTable"]["RouteTableId"]

        if "Tags" in resource:
            target_client.create_tags(Resources=[rt_id], Tags=resource["Tags"])

        # Port Routes
        for route in resource.get("Routes", []):
            if route.get("GatewayId") == "local":
                continue

            route_args = {"RouteTableId": rt_id}
            if "DestinationCidrBlock" in route:
                route_args["DestinationCidrBlock"] = route["DestinationCidrBlock"]
            if "DestinationIpv6CidrBlock" in route:
                route_args["DestinationIpv6CidrBlock"] = route["DestinationIpv6CidrBlock"]

            if route.get("GatewayId"):
                if route["GatewayId"].startswith("igw-"):
                    target_igw_id = self.registry.get_target_id("ec2", "InternetGateway", route["GatewayId"])
                    if target_igw_id:
                        route_args["GatewayId"] = target_igw_id
                # Other gateway types could be added here

            try:
                if "GatewayId" in route_args or "NatGatewayId" in route_args: # Add more as needed
                    target_client.create_route(**route_args)
            except Exception as e:
                print(f"Warning: Could not port route: {e}")

        return rt_id

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_route_tables(RouteTableIds=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["RouteTableId"]

    def get_name(self, resource: dict) -> str:
        for tag in resource.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return "unnamed-route-table"
