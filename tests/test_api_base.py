"""Tests for the base API response handling and error codes."""

from teltasync.api_base import ApiError, ApiResponse


class TestApiError:
    """Test ApiError model functionality."""

    def test_api_error_creation(self):
        """Test creating an ApiError."""
        error = ApiError(code=121, error="Login failed", source="auth", section="login")

        assert error.code == 121
        assert error.error == "Login failed"
        assert error.source == "auth"
        assert error.section == "login"

    def test_api_error_minimal(self):
        """Test creating an ApiError with minimal fields."""
        error = ApiError(code=100, error="Generic error")

        assert error.code == 100
        assert error.error == "Generic error"
        assert error.source is None
        assert error.section is None


class TestApiResponse:
    """Test ApiResponse model functionality."""

    def test_successful_response(self):
        """Test successful API response."""
        response_data = {
            "success": True,
            "data": {"username": "test", "token": "abc123", "expires": 3600},
        }

        response = ApiResponse[dict](**response_data)

        assert response.success is True
        assert response.data == {"username": "test", "token": "abc123", "expires": 3600}
        assert response.errors is None

    def test_error_response(self):
        """Test error API response."""
        response_data = {
            "success": False,
            "errors": [
                {"code": 121, "error": "Login failed", "source": "auth"},
                {"code": 100, "error": "Generic error"},
            ],
        }

        response = ApiResponse[dict](**response_data)

        assert response.success is False
        assert response.data is None
        errors = response.errors
        assert errors is not None
        assert len(errors) == 2
        assert errors[0].code == 121
        assert errors[1].code == 100

    def test_get_error_by_code(self):
        """Test getting error by code."""
        response_data = {
            "success": False,
            "errors": [
                {"code": 121, "error": "Login failed"},
                {"code": 100, "error": "Generic error"},
                {"code": 122, "error": "Invalid structure"},
            ],
        }

        response = ApiResponse[dict](**response_data)

        # Test finding existing error
        error = response.get_error_by_code(121)
        assert error is not None
        assert error.code == 121
        assert error.error == "Login failed"

        # Test finding non-existing error
        error = response.get_error_by_code(999)
        assert error is None

        # Test with no errors
        success_response = ApiResponse[dict](success=True, data={})
        error = success_response.get_error_by_code(121)
        assert error is None

    def test_na_string_conversion_in_response(self):
        """Test that N/A strings are converted to None in API responses."""
        response_data = {
            "success": True,
            "data": {
                "field1": "N/A",
                "field2": "actual_value",
                "nested": {"nested_field": "N/A"},
            },
        }

        response = ApiResponse[dict](**response_data)

        data = response.data
        assert data is not None
        assert data["field1"] is None
        assert data["field2"] == "actual_value"
        assert data["nested"]["nested_field"] is None
