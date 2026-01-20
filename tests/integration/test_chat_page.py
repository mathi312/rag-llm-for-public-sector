import os
from playwright.sync_api import expect

BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")

def test_chat_page_heading(page):
    """Chat page displays correct heading"""
    page.goto(BASE_URL)

    heading = page.get_by_role(
        "heading",
        name="🤖 Digital Assistant - RAG-LLM (Hybrid)"
    )
    heading.wait_for(state="visible")

    expect(heading).to_be_visible()
    expect(heading).to_have_text("🤖 Digital Assistant - RAG-LLM (Hybrid)")

def test_chat_page_has_chat_input(page):
    """Chat page contains chat input field"""
    page.goto(BASE_URL)

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role("heading", name="🤖 Digital Assistant - RAG-LLM (Hybrid)").wait_for(state="visible")

    chat_input = page.get_by_test_id("stChatInputTextArea")

    expect(chat_input).to_be_visible()
    expect(chat_input).to_be_enabled()

def test_chat_page_has_login_page(page):
    """Chat page has navigation to user login page"""
    page.goto(BASE_URL)

    # wait for page to load, more determinstic solution than using networkidle
    page.get_by_role("heading", name="🤖 Digital Assistant - RAG-LLM (Hybrid)").wait_for(state="visible")

    expect(page.get_by_test_id("stToolbar").get_by_text("User")).to_be_visible()

    page.get_by_test_id("stToolbar").get_by_text("User").click()

    expect(page.get_by_role("link", name="Login")).to_be_visible()