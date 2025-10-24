"""Tests for retry logic"""
import pytest
import time
import requests
from unittest.mock import Mock, patch
from api.retry import (
    RetryConfig,
    retry_with_exponential_backoff,
    make_api_request_with_retry
)


def test_retry_config_defaults():
    """Test default retry configuration"""
    config = RetryConfig()

    assert config.max_retries == 3
    assert config.base_delay == 1.0
    assert config.max_delay == 60.0
    assert config.exponential_base == 2.0


def test_retry_config_custom():
    """Test custom retry configuration"""
    config = RetryConfig(
        max_retries=5,
        base_delay=2.0,
        max_delay=30.0,
        exponential_base=3.0
    )

    assert config.max_retries == 5
    assert config.base_delay == 2.0
    assert config.max_delay == 30.0
    assert config.exponential_base == 3.0


def test_retry_success_on_first_attempt():
    """Test successful execution on first attempt"""
    mock_func = Mock(return_value="success")

    result = retry_with_exponential_backoff(mock_func)

    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_success_after_failures():
    """Test successful execution after some failures"""
    mock_func = Mock(side_effect=[
        requests.exceptions.ConnectionError("Connection failed"),
        requests.exceptions.ConnectionError("Connection failed"),
        "success"
    ])

    config = RetryConfig(max_retries=3, base_delay=0.1)
    result = retry_with_exponential_backoff(mock_func, config)

    assert result == "success"
    assert mock_func.call_count == 3


def test_retry_all_attempts_fail():
    """Test when all retry attempts fail"""
    mock_func = Mock(side_effect=requests.exceptions.ConnectionError("Connection failed"))

    config = RetryConfig(max_retries=2, base_delay=0.1)

    with pytest.raises(requests.exceptions.ConnectionError):
        retry_with_exponential_backoff(mock_func, config)

    assert mock_func.call_count == 3  # Initial + 2 retries


def test_retry_exponential_backoff_timing():
    """Test that exponential backoff timing is correct"""
    mock_func = Mock(side_effect=[
        requests.exceptions.ConnectionError("Connection failed"),
        requests.exceptions.ConnectionError("Connection failed"),
        "success"
    ])

    config = RetryConfig(max_retries=2, base_delay=0.1, exponential_base=2.0)

    start_time = time.time()
    result = retry_with_exponential_backoff(mock_func, config)
    elapsed_time = time.time() - start_time

    # Should have delays of ~0.1s and ~0.2s = ~0.3s total
    assert elapsed_time >= 0.3
    assert elapsed_time < 0.5  # Some margin for execution time


def test_make_api_request_success():
    """Test successful API request"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}

    with patch('requests.post', return_value=mock_response):
        response = make_api_request_with_retry(
            "https://api.example.com",
            {"Authorization": "Bearer test"},
            {"data": "test"}
        )

    assert response.status_code == 200
    assert response.json()["result"] == "success"


def test_make_api_request_retry_on_500():
    """Test retrying on 500 error"""
    mock_response_fail = Mock()
    mock_response_fail.status_code = 500

    mock_response_success = Mock()
    mock_response_success.status_code = 200

    with patch('requests.post', side_effect=[mock_response_fail, mock_response_success]):
        config = RetryConfig(max_retries=2, base_delay=0.1)
        response = make_api_request_with_retry(
            "https://api.example.com",
            {"Authorization": "Bearer test"},
            {"data": "test"},
            config=config
        )

    assert response.status_code == 200


def test_make_api_request_no_retry_on_400():
    """Test that 400 errors don't trigger retry"""
    mock_response = Mock()
    mock_response.status_code = 400

    with patch('requests.post', return_value=mock_response):
        response = make_api_request_with_retry(
            "https://api.example.com",
            {"Authorization": "Bearer test"},
            {"data": "test"}
        )

    assert response.status_code == 400
