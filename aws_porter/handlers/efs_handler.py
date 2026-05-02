from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class EFSHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "efs"

    @property
    def resource_type(self) -> str:
        return "FileSystem"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("efs")
        paginator = client.get_paginator("describe_file_systems")
        fs = []
        for page in paginator.paginate():
            fs.extend(page["FileSystems"])
        return fs

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("efs")

        # Check if identical name exists
        name = self.get_name(resource)
        # EFS uses 'CreationToken' for idempotency
        token = resource.get("CreationToken", name)

        args = {
            "CreationToken": token,
            "PerformanceMode": resource["PerformanceMode"],
            "Encrypted": resource["Encrypted"],
            "ThroughputMode": resource["ThroughputMode"],
            "Backup": resource.get("Backup", True)
        }

        if "KmsKeyId" in resource:
             # KMS keys are account specific, skip or map
             pass

        if "ProvisionedThroughputInMibps" in resource:
            args["ProvisionedThroughputInMibps"] = resource["ProvisionedThroughputInMibps"]

        try:
            response = target_client.create_file_system(**args)
            fs_id = response["FileSystemId"]

            if "Tags" in resource:
                target_client.create_tags(FileSystemId=fs_id, Tags=resource["Tags"])

            # Port Mount Targets
            source_client = self.session_manager.get_source_client("efs")
            source_mts = source_client.describe_mount_targets(FileSystemId=resource["FileSystemId"])["MountTargets"]
            for mt in source_mts:
                t_subnet_id = self.registry.get_target_id("ec2", "Subnet", mt["SubnetId"])
                if t_subnet_id:
                    # Map SGs
                    source_sgs = source_client.describe_mount_target_security_groups(MountTargetId=mt["MountTargetId"])["SecurityGroups"]
                    target_sgs = []
                    for sg_id in source_sgs:
                        t_sg_id = self.registry.get_target_id("ec2", "SecurityGroup", sg_id)
                        if t_sg_id: target_sgs.append(t_sg_id)

                    target_client.create_mount_target(
                        FileSystemId=fs_id,
                        SubnetId=t_subnet_id,
                        SecurityGroups=target_sgs
                    )

            return fs_id
        except target_client.exceptions.FileSystemAlreadyExists:
             # Find existing
             existing = target_client.describe_file_systems(CreationToken=token)["FileSystems"][0]
             return existing["FileSystemId"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("efs")
        try:
            target_client.describe_file_systems(FileSystemId=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["FileSystemId"]

    def get_name(self, resource: dict) -> str:
        for tag in resource.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return resource.get("Name", "unnamed-efs")
