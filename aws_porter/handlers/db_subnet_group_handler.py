from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class DBSubnetGroupHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "rds"

    @property
    def resource_type(self) -> str:
        return "DBSubnetGroup"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("rds")
        paginator = client.get_paginator("describe_db_subnet_groups")
        groups = []
        for page in paginator.paginate():
            groups.extend(page["DBSubnetGroups"])
        return groups

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        deps = []
        for subnet in resource["Subnets"]:
            deps.append(("ec2", "Subnet", subnet["SubnetIdentifier"]))
        return deps

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("rds")

        target_subnets = []
        for subnet in resource["Subnets"]:
            t_id = self.registry.get_target_id("ec2", "Subnet", subnet["SubnetIdentifier"])
            if t_id: target_subnets.append(t_id)

        try:
            response = target_client.create_db_subnet_group(
                DBSubnetGroupName=resource["DBSubnetGroupName"],
                DBSubnetGroupDescription=resource["DBSubnetGroupDescription"],
                SubnetIds=target_subnets
            )
            return response["DBSubnetGroup"]["DBSubnetGroupName"]
        except target_client.exceptions.DBSubnetGroupAlreadyExistsFault:
            return resource["DBSubnetGroupName"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("rds")
        try:
            target_client.describe_db_subnet_groups(DBSubnetGroupName=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["DBSubnetGroupName"]

    def get_name(self, resource: dict) -> str:
        return resource["DBSubnetGroupName"]
