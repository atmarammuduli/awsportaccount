import requests
from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class LambdaHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "lambda"

    @property
    def resource_type(self) -> str:
        return "Function"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("lambda")
        return client.list_functions()["Functions"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        deps = []
        role_arn = resource["Role"]
        role_name = role_arn.split("/")[-1]
        deps.append(("iam", "Role", role_name))

        if "VpcConfig" in resource and resource["VpcConfig"].get("VpcId"):
            deps.append(("ec2", "VPC", resource["VpcConfig"]["VpcId"]))

        return deps

    def port(self, resource: dict, overwrite: bool = False) -> str:
        source_client = self.session_manager.get_source_client("lambda")
        target_client = self.session_manager.get_target_client("lambda")

        # Download code from source
        func_name = resource["FunctionName"]
        source_info = source_client.get_function(FunctionName=func_name)
        code_url = source_info["Code"]["Location"]
        code_bytes = requests.get(code_url).content

        # Map role
        source_role_arn = resource["Role"]
        source_role_name = source_role_arn.split("/")[-1]
        target_role_name = self.registry.get_target_id("iam", "Role", source_role_name) or source_role_name

        # We need the full ARN for the target role
        target_sts = self.session_manager.get_target_client("sts")
        target_account = self.session_manager.get_target_account_id()
        target_role_arn = f"arn:aws:iam::{target_account}:role/{target_role_name}"

        # Prepare creation args
        create_args = {
            "FunctionName": func_name,
            "Runtime": resource["Runtime"],
            "Role": target_role_arn,
            "Handler": resource["Handler"],
            "Code": {"ZipFile": code_bytes},
            "Description": resource.get("Description", ""),
            "Timeout": resource["Timeout"],
            "MemorySize": resource["MemorySize"],
            "Publish": True
        }

        if "Environment" in resource:
            create_args["Environment"] = resource["Environment"]

        if "VpcConfig" in resource and resource["VpcConfig"].get("VpcId"):
            source_vpc_id = resource["VpcConfig"]["VpcId"]
            target_vpc_id = self.registry.get_target_id("ec2", "VPC", source_vpc_id)
            if target_vpc_id:
                target_subnets = []
                for s_id in resource["VpcConfig"]["SubnetIds"]:
                    t_id = self.registry.get_target_id("ec2", "Subnet", s_id)
                    if t_id: target_subnets.append(t_id)

                target_sgs = []
                for sg_id in resource["VpcConfig"]["SecurityGroupIds"]:
                    t_sg_id = self.registry.get_target_id("ec2", "SecurityGroup", sg_id)
                    if t_sg_id: target_sgs.append(t_sg_id)

                create_args["VpcConfig"] = {
                    "SubnetIds": target_subnets,
                    "SecurityGroupIds": target_sgs
                }

        response = target_client.create_function(**create_args)
        return response["FunctionName"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("lambda")
        try:
            target_client.get_function(FunctionName=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["FunctionName"]

    def get_name(self, resource: dict) -> str:
        return resource["FunctionName"]
