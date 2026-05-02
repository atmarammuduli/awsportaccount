import json
from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class IAMRoleHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "iam"

    @property
    def resource_type(self) -> str:
        return "Role"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("iam")
        return client.list_roles()["Roles"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return [] # Roles might depend on other roles in policies, but not strictly for creation

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("iam")
        source_account_id = self.session_manager.get_source_account_id()
        target_account_id = self.session_manager.get_target_account_id()

        # Update trust policy with target account ID if necessary
        trust_policy = json.dumps(resource["AssumeRolePolicyDocument"])
        trust_policy = trust_policy.replace(source_account_id, target_account_id)

        try:
            response = target_client.create_role(
                RoleName=resource["RoleName"],
                AssumeRolePolicyDocument=trust_policy,
                Description=resource.get("Description", ""),
                Path=resource["Path"]
            )
            role_name = response["Role"]["RoleName"]

            # Port Managed Policies
            source_client = self.session_manager.get_source_client("iam")
            attached = source_client.list_attached_role_policies(RoleName=resource["RoleName"])["AttachedPolicies"]
            for policy in attached:
                target_client.attach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

            # Port Inline Policies
            inline = source_client.list_role_policies(RoleName=resource["RoleName"])["PolicyNames"]
            for policy_name in inline:
                policy_doc = source_client.get_role_policy(RoleName=resource["RoleName"], PolicyName=policy_name)["PolicyDocument"]
                # Replace Account ID in inline policy
                policy_doc_str = json.dumps(policy_doc).replace(source_account_id, target_account_id)
                target_client.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=policy_doc_str)

            return role_name
        except target_client.exceptions.EntityAlreadyExistsException:
            return resource["RoleName"]

    def verify(self, target_id: str) -> bool:
        target_client = self.session_manager.get_target_client("iam")
        try:
            target_client.get_role(RoleName=target_id)
            return True
        except:
            return False

    def get_id(self, resource: dict) -> str:
        return resource["RoleName"]

    def get_name(self, resource: dict) -> str:
        return resource["RoleName"]
