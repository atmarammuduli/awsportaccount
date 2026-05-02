from abc import ABC, abstractmethod
from typing import List, Any
from aws_porter.core.session_manager import SessionManager
from aws_porter.core.registry import MigrationRegistry

class BaseHandler(ABC):
    def __init__(self, session_manager: SessionManager, registry: MigrationRegistry):
        self.session_manager = session_manager
        self.registry = registry

    @property
    @abstractmethod
    def service_name(self) -> str:
        pass

    @property
    @abstractmethod
    def resource_type(self) -> str:
        pass

    @abstractmethod
    def discover(self) -> List[dict]:
        """List resources in the source account."""
        pass

    @abstractmethod
    def get_dependencies(self, resource: dict) -> List[tuple]:
        """Return a list of (service, resource_type, source_id) dependencies."""
        pass

    @abstractmethod
    def port(self, resource: dict, overwrite: bool = False) -> str:
        """Create the resource in the target account and return the new ID."""
        pass

    @abstractmethod
    def verify(self, target_id: str) -> bool:
        """Verify the resource exists and is functional in the target account."""
        pass

    @abstractmethod
    def get_id(self, resource: dict) -> str:
        """Extract the ID from a resource object."""
        pass

    @abstractmethod
    def get_name(self, resource: dict) -> str:
        """Extract a human-readable name from a resource object."""
        pass
