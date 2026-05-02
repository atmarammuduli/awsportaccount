import pytest
from unittest.mock import MagicMock
from aws_porter.core.session_manager import SessionManager
from aws_porter.core.registry import MigrationRegistry
from aws_porter.handlers.vpc_handler import VPCHandler

def test_vpc_handler_discover():
    session_mgr = MagicMock(spec=SessionManager)
    registry = MagicMock(spec=MigrationRegistry)

    source_client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [{"Vpcs": [{"VpcId": "vpc-123"}]}]
    source_client.get_paginator.return_value = paginator
    session_mgr.get_source_client.return_value = source_client

    handler = VPCHandler(session_mgr, registry)
    vpcs = handler.discover()

    assert len(vpcs) == 1
    assert vpcs[0]["VpcId"] == "vpc-123"

def test_vpc_handler_port_new():
    session_mgr = MagicMock(spec=SessionManager)
    registry = MagicMock(spec=MigrationRegistry)

    target_client = MagicMock()
    target_client.describe_vpcs.return_value = {"Vpcs": []} # No existing
    target_client.create_vpc.return_value = {"Vpc": {"VpcId": "vpc-target"}}
    session_mgr.get_target_client.return_value = target_client

    handler = VPCHandler(session_mgr, registry)
    source_vpc = {"VpcId": "vpc-source", "CidrBlock": "10.0.0.0/16", "InstanceTenancy": "default"}

    target_id = handler.port(source_vpc)

    assert target_id == "vpc-target"
    target_client.create_vpc.assert_called_once_with(CidrBlock="10.0.0.0/16", InstanceTenancy="default")
