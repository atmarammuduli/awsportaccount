from typing import Dict, Any

class MigrationRegistry:
    def __init__(self):
        # Maps (service, resource_type, source_id) -> target_id
        self._mappings: Dict[tuple, str] = {}
        # Stores full metadata if needed
        self._metadata: Dict[tuple, Any] = {}

    def add_mapping(self, service: str, resource_type: str, source_id: str, target_id: str, metadata: Any = None):
        key = (service, resource_type, source_id)
        self._mappings[key] = target_id
        if metadata:
            self._metadata[key] = metadata

    def get_target_id(self, service: str, resource_type: str, source_id: str) -> str:
        return self._mappings.get((service, resource_type, source_id))

    def has_resource(self, service: str, resource_type: str, source_id: str) -> bool:
        return (service, resource_type, source_id) in self._mappings
