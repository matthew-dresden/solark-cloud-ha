"""Shared test fixtures for SolArk Cloud HA integration tests."""

import pytest


@pytest.fixture
def sample_plant_id():
    return "999999"


@pytest.fixture
def sample_username():
    return "testuser@example.com"


@pytest.fixture
def sample_password():
    return "test-secure-pass"


def make_token_response_dict(
    access_token="test-access-token",
    refresh_token="test-refresh-token",
    expires_in=3599,
    scope="station.view",
    token_type="Bearer",
):
    return {
        "code": 0,
        "msg": "Success",
        "data": {
            "access_token": access_token,
            "token_type": token_type,
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "scope": scope,
        },
        "success": True,
    }


def make_energy_year_response(labels=None, months=12, time_prefix="2024-"):
    if labels is None:
        labels = ["Load", "PV", "Export", "Import", "Charge", "Discharge"]
    infos = []
    for label in labels:
        records = []
        for i in range(months):
            records.append(
                {
                    "time": f"{time_prefix}{i + 1:02d}",
                    "value": str(round((i + 1) * 100.5, 1)),
                    "updateTime": None,
                }
            )
        infos.append(
            {
                "unit": "kWh",
                "records": records,
                "label": label,
                "id": None,
                "groupCode": None,
                "name": None,
            }
        )
    return {"code": 0, "msg": "Success", "data": {"infos": infos}, "success": True}


def make_energy_day_response():
    """Create a day response with PV, Battery, SOC, Grid, Load in watts."""
    labels_data = {
        "PV": [(i, max(0, 5000 * (1 - abs(i - 144) / 144))) for i in range(288)],
        "Load": [(i, 2000 + (i % 50) * 20) for i in range(288)],
        "Grid": [(i, -500 + (i % 30) * 50) for i in range(288)],
        "Battery": [(i, 1000 - (i % 40) * 60) for i in range(288)],
        "SOC": [(i, max(10, min(100, 80 - i * 0.2))) for i in range(288)],
    }
    infos = []
    for label, data in labels_data.items():
        unit = "%" if label == "SOC" else "W"
        records = [
            {"time": f"{i // 12:02d}:{(i % 12) * 5:02d}", "value": str(round(v, 1)), "updateTime": None}
            for i, v in data
        ]
        infos.append({"unit": unit, "records": records, "label": label, "id": None, "groupCode": None, "name": None})
    return {"code": 0, "msg": "Success", "data": {"infos": infos}, "success": True}
