import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def api(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["student@mergington.edu"],
        },
        "Art Club": {
            "description": "Explore drawing and painting",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as client:
        yield client, test_activities


def test_root_redirects_to_static_app(api):
    client, _ = api

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(api):
    client, test_activities = api

    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == test_activities


def test_signup_adds_participant(api):
    client, test_activities = api
    email = "new-student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in test_activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(api):
    client, _ = api

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_returns_404_for_unknown_activity(api):
    client, _ = api

    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(api):
    client, test_activities = api
    email = "student@mergington.edu"

    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in test_activities["Chess Club"]["participants"]


def test_unregister_returns_404_for_unknown_activity(api):
    client, _ = api

    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_for_unregistered_participant(api):
    client, _ = api

    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
