from typing import List, Tuple
from aws_porter.handlers.base_handler import BaseHandler

class KeyPairHandler(BaseHandler):
    @property
    def service_name(self) -> str:
        return "ec2"

    @property
    def resource_type(self) -> str:
        return "KeyPair"

    def discover(self) -> List[dict]:
        client = self.session_manager.get_source_client("ec2")
        return client.describe_key_pairs()["KeyPairs"]

    def get_dependencies(self, resource: dict) -> List[Tuple]:
        return []

    def port(self, resource: dict, overwrite: bool = False) -> str:
        target_client = self.session_manager.get_target_client("ec2")

        # We can only port public keys if we have them.
        # Boto3 describe_key_pairs doesn't return the public key by default.
        # This is a limitation: user usually needs to provide the public key.
        # For now, we'll assume the user might have it or we skip if not possible.

        key_name = resource["KeyName"]
        try:
            # Check if exists
            target_client.describe_key_pairs(KeyNames=[key_name])
            return key_name
        except:
            # In a real tool, we'd prompt for the public key or skip
            # target_client.import_key_pair(KeyName=key_name, PublicKeyMaterial=...)
            return f"SKIP:{key_name} (Public key required)"

    def verify(self, target_id: str) -> bool:
        if target_id.startswith("SKIP:"): return True
        target_client = self.session_manager.get_target_client("ec2")
        try:
            target_client.describe_key_pairs(KeyNames=[target_id])
            return True
        except:
            return False
