"""Test configuration for EMS Agent"""

import pytest
import asyncio
import os
from typing import Generator
from unittest.mock import Mock

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['MONGODB_DATABASE'] = 'EMS_Test_Database'


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client for testing"""
    mock_client = Mock()
    mock_db = Mock()
    mock_collection = Mock()
    
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getattr__.return_value = mock_collection
    mock_collection.find.return_value = []
    mock_collection.count_documents.return_value = 0
    
    return mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    return mock_redis


@pytest.fixture
def sample_energy_data():
    """Sample energy data for testing"""
    return {
        "Equipment_ID": "IKC0073",
        "Timestamp": "2024-01-01T12:00:00Z",
        "Active_Power_kW": 3.45,
        "Voltage_V": 231.2,
        "Current_A": 9.6,
        "Power_Factor": 0.95,
        "Temperature_C": 25.3,
        "CFM": 850
    }


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "mongodb_uri": "mongodb://localhost:27017",
        "mongodb_database": "EMS_Test_Database",
        "redis_host": "localhost",
        "redis_port": 6379,
        "environment": "test"
    }
