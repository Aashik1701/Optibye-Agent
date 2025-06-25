"""Unit tests for EMS Query Engine"""

import pytest
from unittest.mock import Mock, patch
from ems_search import EMSQueryEngine


class TestEMSQueryEngine:
    """Test cases for EMS Query Engine"""
    
    @pytest.fixture
    def mock_query_engine(self, mock_mongodb):
        """Create query engine with mocked dependencies"""
        with patch('ems_search.MongoClient', return_value=mock_mongodb):
            engine = EMSQueryEngine()
            return engine
    
    def test_initialization(self, mock_query_engine):
        """Test query engine initialization"""
        assert mock_query_engine is not None
        assert hasattr(mock_query_engine, 'db')
    
    def test_process_simple_query(self, mock_query_engine, mock_mongodb):
        """Test processing a simple query"""
        # Mock collection response
        mock_collection = Mock()
        mock_collection.find.return_value = [
            {
                "Equipment_ID": "IKC0073",
                "Active_Power_kW": 3.45,
                "Voltage_V": 231.2
            }
        ]
        mock_mongodb.__getitem__.return_value.__getattr__.return_value = mock_collection
        
        result = mock_query_engine.process_query("What is the power consumption?")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_system_stats(self, mock_query_engine, mock_mongodb):
        """Test system statistics retrieval"""
        # Mock database stats
        mock_collection = Mock()
        mock_collection.count_documents.return_value = 100
        mock_mongodb.__getitem__.return_value.__getattr__.return_value = mock_collection
        
        stats = mock_query_engine.get_system_stats()
        
        assert isinstance(stats, dict)
        assert 'collections' in stats or 'error' in stats
    
    def test_empty_query(self, mock_query_engine):
        """Test handling of empty query"""
        result = mock_query_engine.process_query("")
        
        assert isinstance(result, str)
        assert "provide" in result.lower() or "specify" in result.lower()
    
    def test_power_consumption_query(self, mock_query_engine, mock_mongodb):
        """Test power consumption specific query"""
        mock_collection = Mock()
        mock_collection.find.return_value = [
            {"Equipment_ID": "IKC0073", "Active_Power_kW": 3.45}
        ]
        mock_mongodb.__getitem__.return_value.__getattr__.return_value = mock_collection
        
        result = mock_query_engine.process_query("power consumption for IKC0073")
        
        assert isinstance(result, str)
        assert len(result) > 0
