from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class SecurityGroupHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "SecurityGroup"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        return client.describe_security_groups()["SecurityGroups"]

    def get_dependencies(self, resource: dict) -> List[tuple]:
        return [("ec2", "VPC", resource["VpcId"])]

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")
        target_vpc_id = self.registry.get_target_id("ec2", "VPC", resource["VpcId"])

        if resource["GroupName"] == "default":
            # Handle default security group differently - it usually exists
            sgs = target_client.describe_security_groups(Filters=[
                {"Name": "vpc-id", "Values": [target_vpc_id]},
                {"Name": "group-name", "Values": ["default"]}
            ])["SecurityGroups"]
            return sgs[0]["GroupId"]

        # Check for existing
        existing = self._find_existing_by_name(target_client, target_vpc_id, resource["GroupName"])
        if existing:
            return existing["GroupId"]

        response = target_client.create_security_group(
            Description=resource["Description"],
            GroupName=resource["GroupName"],
            VpcId=target_vpc_id
        )
        sg_id = response["GroupId"]

        # Port Inbound Rules
        if "IpPermissions" in resource and resource["IpPermissions"]:
            self._port_rules(target_client, sg_id, resource["IpPermissions"], "ingress")

        # Port Outbound Rules
        if "IpPermissionsEgress" in resource and resource["IpPermissionsEgress"]:
            self._port_rules(target_client, sg_id, resource["IpPermissionsEgress"], "egress")

        return sg_id

    def _port_rules(self, client, sg_id, permissions, direction):
        target_account_id = self.session_manager.get_target_account_id()
        clean_permissions = []
        for perm in permissions:
            new_perm = perm.copy()
            # Handle UserIdGroupPairs (references to other SGs)
            if "UserIdGroupPairs" in new_perm:
                new_pairs = []
                for pair in new_perm["UserIdGroupPairs"]:
                    new_pair = pair.copy()
                    # Update Account ID for the pair if it's the target account's reference
                    new_pair["UserId"] = target_account_id

                    if "GroupId" in new_pair:
                        target_sg_id = self.registry.get_target_id("ec2", "SecurityGroup", new_pair["GroupId"])
                        if target_sg_id:
                            new_pair["GroupId"] = target_sg_id
                    new_pairs.append(new_pair)
                new_perm["UserIdGroupPairs"] = new_pairs
            clean_permissions.append(new_perm)

        if direction == "ingress":
            client.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=clean_permissions)
        else:
            client.authorize_security_group_egress(GroupId=sg_id, IpPermissions=clean_permissions)

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_security_groups(GroupIds=[target_id])
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["GroupId"]

    def get_name(self, resource: dict) -> str:
        return resource["GroupName"]

    def _find_existing_by_name(self, client, vpc_id, name: str):
        sgs = client.describe_security_groups(Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "group-name", "Values": [name]}
        ])["SecurityGroups"]
        return sgs[0] if sgs else None
