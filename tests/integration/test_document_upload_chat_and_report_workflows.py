import pytest
import os
import re

from pathlib import Path
from playwright.sync_api import expect
from test_login import navigate_to_login_page, login, seed_test_user, pb

FILEPATH = Path(__file__).parent / "test_data" / "lebensunterhalt.pdf"

BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")

@pytest.fixture(autouse=True)
def logout(page):
    yield # return directly to the test

    # this runs after each test in this module
    try:
        page.get_by_test_id("stBaseButton-primary").click()
    except:
        # already logged out, so do nothing
        pass

def test_document_upload_and_build_index(page, navigate_to_login_page, seed_test_user):
    login(page, "testuser@testuser.de", "12345678")

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role("heading", name="🤖 Digital Assistant - RAG-LLM (Hybrid)").wait_for(state="visible")

    admin_sidebar = page.get_by_role("tab", name="Administration")
    expect(admin_sidebar).to_be_visible()
    admin_sidebar.click()

    data_source = page.get_by_role("heading", name="Data Sources")
    expect(data_source).to_be_visible()

    # locate file upload input and choose the second one, because the first one is for the id upload
    file_input = page.locator('input[data-testid="stFileUploaderDropzoneInput"]').nth(1)
    file_input.wait_for(state="attached")

    if not os.path.exists(FILEPATH):
        raise FileNotFoundError(f"Test file not found: {FILEPATH}")

    file_input.set_input_files(FILEPATH)

    expect(page.get_by_text("lebensunterhalt", exact=False)).to_be_visible()
    
    # dont include the files in the data dir
    locator = page.get_by_text("✅ Found")

    if locator.is_visible():
        page.locator(".st-fh").click()
    
    # select rebuild index
    index_mode = page.locator('div[aria-label="Index mode"] label[data-baseweb="radio"]:has(input[value="1"])')
    index_mode.click()
    
    page.get_by_role("button", name="Build / Update Index").click()

    page.get_by_text("Index built successfully!").wait_for(state="visible", timeout=180000)

def test_chat(page):
    page.goto(BASE_URL)

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role("heading", name="🤖 Digital Assistant - RAG-LLM (Hybrid)").wait_for(state="visible")

    chat_input = page.get_by_test_id("stChatInputTextArea")
    expect(chat_input).to_be_editable()
    chat_input.fill("wann ist der lebensunterhalt gesichert?")
    
    page.get_by_test_id("stChatInputSubmitButton").click()

    # wait for answer to be visible
    page.get_by_text("smart_toyDer Lebensunterhalt").wait_for(state="visible", timeout=180000)
    page.get_by_text("Der Lebensunterhalt ist").wait_for(state="visible", timeout=180000)

    # check that the correct source is displayed
    page.locator("button", has_text=".pdf").first.click()
    expect(page.get_by_test_id("stDialog").get_by_test_id("stLayoutWrapper")).to_contain_text(
        "Paragraph 17 gilt der Lebensunterhalt als gesichert, wenn Mittel entsprechend dem Bedarf zuzüglich eines Zuschlags von " +
        "zehn Prozent zur Verfügung stehen. Die jährlichen Mindestbeträge werden vom Bundesministerium des Innern im Bundesanzeiger bekannt gemacht.")
    
    page.get_by_test_id("stDialog").get_by_test_id("stBaseButton-secondary").click()
    
    # test the print report of the chat
    print_rebort_btn = page.get_by_role("button", name="Print Report")
    expect(print_rebort_btn).to_be_visible()
    print_rebort_btn.click()

    expect(page.get_by_test_id("stAlertContentError")).to_contain_text("Printer currently not available. Alternatively you can send the report per mail")

    page.get_by_role("textbox", name="Email").fill("test@mail.de")
    page.get_by_test_id("stDialog").get_by_test_id("stBaseButton-secondary").click()

    expect(page.get_by_test_id("stAlertContentSuccess")).to_contain_text("Email sent successfully.")

def test_print_report_shows_error_when_no_chat_exists(page):
    """Test error message when printing a report without chat history."""
    page.goto(BASE_URL)

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role("heading", name="🤖 Digital Assistant - RAG-LLM (Hybrid)").wait_for(state="visible")

    print_rebort_btn = page.get_by_role("button", name="Print Report")
    expect(print_rebort_btn).to_be_visible()

    print_rebort_btn.click()
    expect(page.get_by_test_id("stSidebarUserContent")).to_contain_text("No content available for this report. Please start a conversation and try again.")
