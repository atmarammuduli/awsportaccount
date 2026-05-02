from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class LaunchTemplateHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "LaunchTemplate"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        paginator = client.get_paginator("describe_launch_templates")
        lts = []
        for page in paginator.paginate():
            lts.extend(page["LaunchTemplates"])
        return lts

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")

        # Fetch the default version data
        source_client = self.session_manager.get_source_client("ec2")
        version_data = source_client.describe_launch_template_versions(
            LaunchTemplateId=resource["LaunchTemplateId"],
            Versions=[str(resource["DefaultVersionNumber"])]
        )["LaunchTemplateVersions"][0]["LaunchTemplateData"]

        # Clean up data (remove IDs that won't match)
        version_data.pop("KernelId", None)
        version_data.pop("RamdiskId", None)

        # Map Security Groups if present
        if "SecurityGroupIds" in version_data:
            target_sgs = []
            for sg_id in version_data["SecurityGroupIds"]:
                t_id = self.registry.get_target_id("ec2", "SecurityGroup", sg_id)
                if t_id: target_sgs.append(t_id)
            version_data["SecurityGroupIds"] = target_sgs

        try:
            response = target_client.create_launch_template(
                LaunchTemplateName=resource["LaunchTemplateName"],
                LaunchTemplateData=version_data
            )
            return response["LaunchTemplate"]["LaunchTemplateId"]
        except target_client.exceptions.ClientError as e:
            if "already exists" in str(e):
                return resource["LaunchTemplateName"]
            raise e

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            if target_id.startswith("lt-"):
                target_client.describe_launch_templates(LaunchTemplateIds=[target_id])
            else:
                target_client.describe_launch_templates(LaunchTemplateNames=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["LaunchTemplateId"]

    def get_name(self, resource: dict) -> str:
        return resource["LaunchTemplateName"]
