import os

import pytest
from playwright.sync_api import expect

from test_login import login, navigate_to_login_page, pb

BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")


@pytest.fixture(scope="function")
def seed_non_admin_user(pb):
    email = "nonadmin@testuser.de"

    try:
        users = pb.collection("users").get_full_list(
            query_params={"filter": f'email="{email}"'}
        )
        for user in users:
            pb.collection("users").delete(user.id)
    except Exception:
        pass

    pb.collection("users").create(
        {
            "email": email,
            "password": "12345678",
            "passwordConfirm": "12345678",
            "emailVisibility": True,
            "admin": False,
        }
    )

    yield email

    users = pb.collection("users").get_full_list(
        query_params={"filter": f'email="{email}"'}
    )
    for user in users:
        pb.collection("users").delete(user.id)


def test_non_admin_cannot_see_admin_navigation(
    page, navigate_to_login_page, seed_non_admin_user
):
    login(page, seed_non_admin_user, "12345678")

    page.get_by_role(
        "heading",
        name="🤖 Digital Assistant - RAG-LLM (Hybrid)",
    ).wait_for(state="visible")

    toolbar = page.get_by_test_id("stToolbar")
    expect(toolbar.get_by_text("Documentmanager")).not_to_be_visible()
    expect(toolbar.get_by_text("Logs")).not_to_be_visible()

    page.goto(BASE_URL)
    expect(page.get_by_role("tab", name="Administration")).not_to_be_visible()
