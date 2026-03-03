"""End-to-End tests for document management page."""
import os
from pathlib import Path

import pytest

from test_login import navigate_to_login_page, login, seed_test_user, pb
from playwright.sync_api import expect

BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")
FILEPATH = Path(__file__).parent / "test_data" / "lebensunterhalt.pdf"

@pytest.fixture(autouse=True)
def setup(page, navigate_to_login_page, seed_test_user):
    """Setup the test environment login as a admin and after the test ran logout again"""
    login(page, "testuser@testuser.de", "12345678")

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role(
        "heading", 
        name="🤖 Digital Assistant - RAG-LLM (Hybrid)"
    ).wait_for(state="visible")

    yield # return to the test

    # this runs after each test in this module
    try:
        page.goto(BASE_URL)

        page.get_by_role(
            "heading", 
            name="🤖 Digital Assistant - RAG-LLM (Hybrid)"
        ).wait_for(state="visible", timeout=5000)

        page.locator("summary").filter(has_text="testuser@testuser").click()
        page.get_by_test_id("stBaseButton-primary").click()
    except TimeoutError:
        # already logged out or page didn't load, so do nothing
        pass
    except (AttributeError, AssertionError) as e:
        # Log unexpected errors for debugging
        print(f"Logout failed: {e}")

def test_document_management_upload_success(page):
    """Test the document upload on the document management page"""
    # navigate to document manager page
    document_manager = page.get_by_test_id("stToolbar").get_by_text("Documentmanager")
    expect(document_manager).to_be_visible()
    document_manager.click()

    document_manager_link = page.get_by_role("link", name="Document Manager")
    expect(document_manager_link).to_be_visible()
    document_manager_link.click()

    expect(page.get_by_label("Document Management")).to_contain_text("3. Document Management")
    expect(page.get_by_role("button", name="Upload New Document")).to_be_visible()

    page.get_by_role("button", name="Upload New Document").click()
    expect(page.get_by_text("Upload Document")).to_be_visible()

    page.get_by_role("textbox", name="Document Title").fill("lebensunterhalt document")
    file_input = page.locator('input[data-testid="stFileUploaderDropzoneInput"]').nth(0)
    file_input.wait_for(state="attached")

    if not os.path.exists(FILEPATH):
        raise FileNotFoundError(f"Test file not found: {FILEPATH}")

    file_input.set_input_files(FILEPATH)

    page.get_by_text("Choose options").click()
    page.get_by_test_id("stSelectboxVirtualDropdown").get_by_text("id-card").click()

    page.get_by_test_id("stDialog").get_by_role("button", name="Upload").click()

    # check name of the document and that the file is the expected file
    expect(page.get_by_text("lebensunterhalt document")).to_be_visible()
    expect(page.get_by_text("lebensunterhalt.pdf")).to_be_visible()

    expect(page.get_by_test_id("stBaseButton-secondary").nth(4)).to_be_visible()
    expect(page.get_by_test_id("stBaseButton-secondary").nth(5)).to_be_visible()
    expect(page.get_by_role("button", name="🗑️ Delete").nth(1)).to_be_visible()

    # delete file
    page.get_by_role("button", name="🗑️ Delete").nth(1).click()

    expect(page.get_by_text("Confirm Delete Document")).to_be_visible()
    expect(page.get_by_text("Do you really want to delete")).to_be_visible()

    page.get_by_role("button", name="Yes, delete").click()
    # make sure delete worked
    expect(page.get_by_text("lebensunterhalt document")).not_to_be_visible()
