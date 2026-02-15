import os
import pytest

from playwright.sync_api import expect
from pocketbase import PocketBase

BASE_URL = os.getenv("BASE_URL", "http://localhost:8501") 

@pytest.fixture
def navigate_to_login_page(page):
    """Navigate from the home page to the login page"""
    page.goto(BASE_URL)

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role("heading", name="🤖 Digital Assistant - RAG-LLM (Hybrid)").wait_for(state="visible")

    expect(page.get_by_test_id("stToolbar")).to_be_visible()

    user_menu = page.get_by_test_id("stToolbar").get_by_text("User")
    expect(user_menu).to_be_visible()
    user_menu.click()

    login_link = page.get_by_role("link", name="Login")
    expect(login_link).to_be_visible()
    login_link.click()

    # Assert we are actually on the login screen
    expect(page.get_by_role("textbox", name="E-Mail")).to_be_visible()
    expect(page.get_by_role("textbox", name="Password")).to_be_visible()

@pytest.fixture(scope="session")
def pb():
    """Authenticated PocketBase admin client"""
    pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
    client = PocketBase(pb_url)

    client.admins.auth_with_password(
        os.getenv("POCKETBASE_ADMIN_USERNAME"), os.getenv("POCKETBASE_ADMIN_PASSWORD")
    )

    return client

@pytest.fixture(scope="function")
def seed_test_user(pb):
    """Ensure a clean test user exists before test runs"""

    email = "testuser@testuser.de"

    # Delete existing test user if present
    try:
        users = pb.collection("users").get_full_list(
            query_params={"filter": f'email="{email}"'}
        )
        for user in users:
            pb.collection("users").delete(user.id)
    except Exception:
        pass

    # Create fresh user
    pb.collection("users").create({
        "email": email,
        "password": "12345678",
        "passwordConfirm": "12345678",
        "emailVisibility": True,
        "admin": True
    })

    yield

    # Cleanup after test
    users = pb.collection("users").get_full_list(
        query_params={"filter": f'email="{email}"'}
    )
    for user in users:
        pb.collection("users").delete(user.id)

def login(page, email: str, password: str):
    """Login helper to fill in the login form and submit"""
    page.get_by_role("textbox", name="E-Mail").fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_test_id("stBaseButton-secondaryFormSubmit").click()


def test_login_fail(page, navigate_to_login_page, seed_test_user):
    """Test display of error message when authentication failed"""
    login(page, "test@gmail.com", "blabla")

    error_message = page.get_by_text(
        "Authentication failed", exact=False
    )

    expect(error_message).to_be_visible()

def test_login_success(page, navigate_to_login_page, seed_test_user):
    """Test user login and logout"""
    login(page, "testuser@testuser.de", "12345678")

    expect(page.get_by_test_id("stSidebarUserContent").get_by_role("link")).to_contain_text("testuser@testuser.de")
    page.locator("summary").filter(has_text="testuser@testuser").click()

    expect(page.get_by_text("Role: Admin")).to_be_visible()

    expect(page.get_by_test_id("stBaseButton-primary")).to_be_visible()
    page.get_by_test_id("stBaseButton-primary").click()

    # Assert logout worked
    expect(page.get_by_test_id("stToolbar").get_by_text("User")).to_be_visible()
