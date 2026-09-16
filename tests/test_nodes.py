import configparser

import pytest

from elvis_botnet.manager import Manager
from elvis_botnet.worker import Worker


def make_config(node_type: str, **peers: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config["node"] = {"type": node_type}
    if peers:
        config["peers"] = peers
    return config


@pytest.fixture
def manager_client():
    config = make_config("manager", managers="", workers="172.28.0.12,172.28.0.13")
    manager = Manager(config)
    return manager, manager.app.test_client()


@pytest.fixture
def worker_client():
    config = make_config("worker", manager="172.28.0.11")
    worker = Worker(config)
    return worker, worker.app.test_client()


def test_manager_health(manager_client):
    _, client = manager_client
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_worker_health(worker_client):
    _, client = worker_client
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_manager_info_reports_node_type_and_system_details(manager_client):
    _, client = manager_client
    body = client.get("/info").get_json()
    assert body["node_type"] == "manager"
    assert body["hostname"]
    assert body["ip_address"]
    assert body["commands_received"] == 0
    assert body["commands_completed"] == 0


def test_worker_info_reports_node_type(worker_client):
    _, client = worker_client
    body = client.get("/info").get_json()
    assert body["node_type"] == "worker"


def test_manager_status_includes_peer_lists(manager_client):
    _, client = manager_client
    body = client.get("/status").get_json()
    assert body["managers"] == []
    assert body["workers"] == ["172.28.0.12", "172.28.0.13"]
    assert body["node_type"] == "manager"


def test_worker_status_includes_manager_ip(worker_client):
    _, client = worker_client
    body = client.get("/status").get_json()
    assert body["manager"] == "172.28.0.11"
    assert body["node_type"] == "worker"
