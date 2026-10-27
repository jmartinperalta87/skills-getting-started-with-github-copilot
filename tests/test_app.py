from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app, follow_redirects=False)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_activities))

    yield

    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data():
    # Arrange
    expected_names = set(app_module.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json()) == expected_names


def test_signup_adds_student_to_activity():
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_returns_not_found_for_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_bad_request_for_duplicate_student():
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_unregister_removes_student_from_activity():
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"
    app_module.activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_returns_not_found_for_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_student():
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
