from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class RDSHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "rds"

    @property
    def resource_type(self) -> str:
        return "DBInstance"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("rds")
        paginator = client.get_paginator("describe_db_instances")
        instances = []
        for page in paginator.paginate():
            instances.extend(page["DBInstances"])
        return instances

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        deps = []
        if resource.get("DBSubnetGroup"):
            deps.append(("rds", "DBSubnetGroup", resource["DBSubnetGroup"]["DBSubnetGroupName"]))
        if resource.get("VpcSecurityGroups"):
            for sg in resource["VpcSecurityGroups"]:
                deps.append(("ec2", "SecurityGroup", sg["VpcSecurityGroupId"]))
        return deps

    def port(self, resource: dict, overwrite: bool = False) -> str:
        from rich.prompt import Prompt
        target_client = self.session_manager.get_target_client("rds")

        password = Prompt.ask(f"Enter Master Password for RDS instance [bold]{resource['DBInstanceIdentifier']}[/bold]", password=True)

        args = {
            "DBInstanceIdentifier": resource["DBInstanceIdentifier"],
            "Engine": resource["Engine"],
            "DBInstanceClass": resource["DBInstanceClass"],
            "AllocatedStorage": resource["AllocatedStorage"],
            "MasterUsername": resource["MasterUsername"],
            "MasterUserPassword": password,
            "BackupRetentionPeriod": resource["BackupRetentionPeriod"],
            "MultiAZ": resource["MultiAZ"],
            "EngineVersion": resource["EngineVersion"],
            "AutoMinorVersionUpgrade": resource["AutoMinorVersionUpgrade"],
            "PubliclyAccessible": resource["PubliclyAccessible"]
        }

        # Map Subnet Group
        if resource.get("DBSubnetGroup"):
            t_sng = self.registry.get_target_id("rds", "DBSubnetGroup", resource["DBSubnetGroup"]["DBSubnetGroupName"])
            if t_sng:
                args["DBSubnetGroupName"] = t_sng

        # Map Security Groups
        if "VpcSecurityGroups" in resource:
            target_sgs = []
            for sg in resource["VpcSecurityGroups"]:
                t_sg_id = self.registry.get_target_id("ec2", "SecurityGroup", sg["VpcSecurityGroupId"])
                if t_sg_id: target_sgs.append(t_sg_id)
            if target_sgs:
                args["VpcSecurityGroupIds"] = target_sgs

        try:
            response = target_client.create_db_instance(**args)
            return response["DBInstance"]["DBInstanceIdentifier"]
        except target_client.exceptions.DBInstanceAlreadyExistsFault:
            return resource["DBInstanceIdentifier"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("rds")
        try:
            target_client.describe_db_instances(DBInstanceIdentifier=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["DBInstanceIdentifier"]

    def get_name(self, resource: dict) -> str:
        return resource["DBInstanceIdentifier"]
