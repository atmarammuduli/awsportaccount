import pytest
from unittest.mock import MagicMock
from aws_porter.core.engine import MigrationEngine
from aws_porter.handlers.base_handler import BaseHandler

class MockHandler(BaseHandler):
    @property
    def service_name(self): return "mock"
    @property
    def resource_type(self): return "Resource"
    def discover(self): return [{"Id": "r-1"}]
    def get_dependencies(self, res): return []
    def port(self, res, overwrite=False): return "r-1-target"
    def verify(self, tid): return True
    def get_id(self, res): return res["Id"]
    def get_name(self, res): return "MockRes"

def test_engine_port_with_dependencies():
    session_mgr = MagicMock()
    engine = MigrationEngine(session_mgr)
    handler = MockHandler(session_mgr, engine.registry)

    target_id = engine._port_with_dependencies(handler, {"Id": "r-1"})

    assert target_id == "r-1-target"
    assert engine.registry.get_target_id("mock", "Resource", "r-1") == "r-1-target"
