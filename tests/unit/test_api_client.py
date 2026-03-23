"""Tests for the SolarkCloud API client."""

import httpx
import pytest
import respx

from custom_components.solark_cloud.api_client import (
    SolarkCloudApiClient,
    SolarkCloudApiError,
    SolarkCloudAuthError,
)
from tests.conftest import make_energy_day_response, make_energy_year_response, make_token_response_dict


class TestSolarkCloudApiClient:
    @pytest.fixture
    def api_url(self):
        return "https://test.solarkcloud.example.com"

    @pytest.fixture
    def client(self, api_url, sample_username, sample_password):
        return SolarkCloudApiClient(
            username=sample_username,
            password=sample_password,
            api_url=api_url,
            tz_name="America/Detroit",
        )

    @respx.mock
    async def test_authenticate_success(self, client, api_url):
        token_data = make_token_response_dict()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        await client.async_init()
        await client.async_authenticate()
        assert client._access_token == token_data["data"]["access_token"]
        await client.async_close()

    @respx.mock
    async def test_authenticate_http_error(self, client, api_url):
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(401, json={"error": "unauthorized"}))
        await client.async_init()
        with pytest.raises(httpx.HTTPStatusError):
            await client.async_authenticate()
        await client.async_close()

    @respx.mock
    async def test_authenticate_api_failure(self, client, api_url):
        resp = {
            "code": 1,
            "msg": "Invalid credentials",
            "data": {
                "access_token": "",
                "token_type": "",
                "expires_in": 0,
                "refresh_token": "",
                "scope": "",
            },
            "success": False,
        }
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=resp))
        await client.async_init()
        with pytest.raises(SolarkCloudAuthError, match="Authentication failed"):
            await client.async_authenticate()
        await client.async_close()

    @respx.mock
    async def test_get_energy_year(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        year_data = make_energy_year_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/year").mock(
            return_value=httpx.Response(200, json=year_data)
        )
        await client.async_init()
        result = await client.async_get_energy_year(sample_plant_id, "2024")
        assert result["success"] is True
        assert len(result["data"]["infos"]) == 6
        await client.async_close()

    @respx.mock
    async def test_get_energy_month(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        month_data = make_energy_year_response(months=30, time_prefix="2024-07-")
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/month").mock(
            return_value=httpx.Response(200, json=month_data)
        )
        await client.async_init()
        result = await client.async_get_energy_month(sample_plant_id, "2024-07-01")
        assert result["success"] is True
        await client.async_close()

    @respx.mock
    async def test_get_energy_day(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        day_data = make_energy_day_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/day").mock(
            return_value=httpx.Response(200, json=day_data)
        )
        await client.async_init()
        result = await client.async_get_energy_day(sample_plant_id, "2024-07-15")
        assert result["success"] is True
        assert len(result["data"]["infos"]) == 5
        await client.async_close()

    @respx.mock
    async def test_get_current_month_energy(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        year_data = make_energy_year_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/year").mock(
            return_value=httpx.Response(200, json=year_data)
        )
        await client.async_init()
        result = await client.async_get_current_month_energy(sample_plant_id)
        assert isinstance(result, dict)
        await client.async_close()

    @respx.mock
    async def test_get_current_year_energy(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        year_data = make_energy_year_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/year").mock(
            return_value=httpx.Response(200, json=year_data)
        )
        await client.async_init()
        result = await client.async_get_current_year_energy(sample_plant_id)
        assert isinstance(result, dict)
        # Year totals should sum all months
        for label in result:
            assert result[label] > 0
        await client.async_close()

    @respx.mock
    async def test_get_today_energy(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        day_data = make_energy_day_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/day").mock(
            return_value=httpx.Response(200, json=day_data)
        )
        await client.async_init()
        result = await client.async_get_today_energy(sample_plant_id)
        assert "PV" in result
        assert "Load" in result
        assert "Import" in result
        assert "Export" in result
        assert "Charge" in result
        assert "Discharge" in result
        # All values should be non-negative kWh
        for val in result.values():
            assert val >= 0
        await client.async_close()

    @respx.mock
    async def test_get_realtime_power(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        day_data = make_energy_day_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/day").mock(
            return_value=httpx.Response(200, json=day_data)
        )
        await client.async_init()
        result = await client.async_get_realtime_power(sample_plant_id)
        assert "pv_power" in result
        assert "load_power" in result
        assert "grid_power" in result
        assert "battery_power" in result
        assert "battery_soc" in result
        await client.async_close()

    def test_now_uses_timezone(self):
        client = SolarkCloudApiClient("u", "p", tz_name="America/Detroit")
        now = client._now()
        assert now.tzinfo is not None
        tz_name = str(now.tzinfo)
        assert "Detroit" in tz_name or "Eastern" in tz_name or "EST" in tz_name or "EDT" in tz_name

    def test_now_uses_local_when_empty(self):
        client = SolarkCloudApiClient("u", "p", tz_name="")
        now = client._now()
        assert now.tzinfo is not None

    @respx.mock
    async def test_get_today_empty_data(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        empty_day = {"code": 0, "msg": "Success", "data": {"infos": []}, "success": True}
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/day").mock(
            return_value=httpx.Response(200, json=empty_day)
        )
        await client.async_init()
        result = await client.async_get_today_energy(sample_plant_id)
        assert result == {}
        await client.async_close()

    @respx.mock
    async def test_api_error_on_failed_get(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        failed = {"code": 1, "msg": "Server error", "data": {}, "success": False}
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/year").mock(
            return_value=httpx.Response(200, json=failed)
        )
        await client.async_init()
        with pytest.raises(SolarkCloudApiError, match="API request failed"):
            await client.async_get_energy_year(sample_plant_id, "2024")
        await client.async_close()

    @respx.mock
    async def test_get_realtime_power_empty_data(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        empty_day = {"code": 0, "msg": "Success", "data": {"infos": []}, "success": True}
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/day").mock(
            return_value=httpx.Response(200, json=empty_day)
        )
        await client.async_init()
        result = await client.async_get_realtime_power(sample_plant_id)
        assert result == {}
        await client.async_close()

    @respx.mock
    async def test_get_year_energy_structured(self, client, api_url, sample_plant_id):
        token_data = make_token_response_dict()
        year_data = make_energy_year_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/year").mock(
            return_value=httpx.Response(200, json=year_data)
        )
        await client.async_init()
        result = await client.async_get_year_energy(sample_plant_id, "2024")
        # Should be keyed by month with labels as sub-keys
        assert isinstance(result, dict)
        assert len(result) > 0
        for _month_key, labels in result.items():
            assert isinstance(labels, dict)
            assert "Load" in labels
        await client.async_close()

    @respx.mock
    async def test_auto_init_on_authenticate(self, api_url, sample_username, sample_password):
        """Client auto-initializes httpx client if async_init was not called."""
        client = SolarkCloudApiClient(
            username=sample_username,
            password=sample_password,
            api_url=api_url,
            tz_name="America/Detroit",
        )
        token_data = make_token_response_dict()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        # Do NOT call async_init; authenticate should handle it
        await client.async_authenticate()
        assert client._access_token == token_data["data"]["access_token"]
        await client.async_close()

    @respx.mock
    async def test_auto_authenticate_on_get(self, client, api_url, sample_plant_id):
        """_async_get auto-authenticates if no token is present."""
        token_data = make_token_response_dict()
        year_data = make_energy_year_response()
        respx.post(f"{api_url}/oauth/token").mock(return_value=httpx.Response(200, json=token_data))
        respx.get(url__startswith=f"{api_url}/api/v1/plant/energy/{sample_plant_id}/year").mock(
            return_value=httpx.Response(200, json=year_data)
        )
        # Do NOT call async_init or authenticate; _async_get should handle both
        result = await client.async_get_energy_year(sample_plant_id, "2024")
        assert result["success"] is True
        await client.async_close()

    def test_energy_url_construction(self, client, sample_plant_id):
        url = client._energy_url(sample_plant_id, "year", "2024")
        assert f"/api/v1/plant/energy/{sample_plant_id}/year" in url
        assert "date=2024" in url
        assert f"id={sample_plant_id}" in url
        assert "lan=en" in url

    async def test_async_close_idempotent(self, client):
        """Closing a client that was never initialized should not raise."""
        await client.async_close()
        # Call again to verify idempotent behavior
        await client.async_close()
