# 🤖 Modular Hybrid RAG Assistant - Installation & Setup Guide

## 1. Overview

This project provides a private, containerized, and hybrid **Retrieval-Augmented Generation (RAG)** application. It enables users to chat with PDF and DOCX documents sourced from both a static local directory and ad-hoc user uploads.

It supports a **Hybrid AI Architecture**:
1.  **Local & Private:** Run entirely offline using open-source LLMs (Llama 3, Mistral) via Ollama.
2.  **Cloud Power:** Switch to OpenAI (GPT-4o) instantly for higher performance when privacy is less critical.

## 2. System Requirements

Before starting, ensure your system meets the following requirements.

### 2.1. Hardware (Recommended for Local Mode)
*   **RAM:** Minimum **8GB** (16GB recommended).
    *   *Note: Running local LLMs requires significant memory. If you only use OpenAI mode, 4GB is sufficient.*
*   **CPU:** Modern multi-core processor (Intel i5/i7/i9 or AMD Ryzen 5/7/9).
*   **Disk Space:** At least **10GB** free space (for Docker images and AI models).

### 2.2. Software Dependencies
You must install the following tools manually before running the application.

1.  **Docker Desktop** (or Docker Engine on Linux)
    *   **Version:** 24.0.0 or higher.
    *   **Download:** https://www.docker.com/products/docker-desktop/
    *   *Windows Users:* Ensure WSL 2 backend is enabled during installation.

2.  **Git**
    *   **Version:** Any recent version.
    *   **Download:** https://git-scm.com/downloads

3.  **(Optional) Visual Studio Code**
    *   **Extension:** "Dev Containers" or "WSL" extension is highly recommended for Windows users.

4.  **(Optional) OpenAI API Key**
    *   Required only if you intend to use the "OpenAI" provider mode.
    *   Get one here: https://platform.openai.com/api-keys

---

## 3. Installation Guide (Step-by-Step)

This guide assumes you have the source code (Python files) but need to set up the environment from scratch.

### Step 1: Verify Docker Installation
Open your terminal (PowerShell, Command Prompt, or Terminal) and run:

    docker --version
    docker compose version

*   If these commands fail, please install Docker Desktop first.
*   *Linux Users:* Ensure your user is in the `docker` group so you don't need `sudo`.

### Step 2: Prepare the Project Directory
1.  Place all provided source files (`app.py`, `Dockerfile`, `docker-compose.yml`, etc.) into a new folder named `modular-rag-app`.
2.  Open your terminal in this folder.
3.  Create the required data directory:

    mkdir data

4.  (Optional) Copy any PDF or DOCX files you want to auto-index into this `data/` folder.

### Step 3: Build the Application
Run the Docker Compose build command. This process creates the Python environment inside a container, installs `python 3.12`, and downloads all libraries defined in `requirements.txt`.

    docker compose build --no-cache

*   *Note: This may take 2-5 minutes depending on your internet speed.*

### Step 4: Start the Services
Launch the application stack in detached mode (background):

    docker compose up -d

*   This starts two containers:
    1.  **rag-app:** The Streamlit frontend (Port 8501).
    2.  **ollama:** The local AI inference engine (Port 11434).

### Step 5: Download the AI Model (Critical First-Time Step)
By default, the local AI engine is empty. You must download a model (e.g., `llama3.2`) for the local mode to work.

    docker exec -it ollama ollama pull llama3.2

*   *Note: This downloads ~2.0 GB of data.*
*   *Alternative:* You can pull `mistral` or `llama3` if you prefer those models.

---

## 4. Usage Guide

### 4.1. Accessing the App
Open your web browser and navigate to:
👉 http://localhost:8501

### 4.2. Configuration (Sidebar)
*   **Provider:**
    *   **Local (Ollama):** Free, private, runs offline. Uses your PC's resources.
    *   **OpenAI:** Paid, cloud-based, extremely fast. Requires an API Key (`sk-...`).
*   **Model:** Select the specific model (e.g., `llama3.2` or `gpt-4o`).

### 4.3. Ingesting Data
1.  **Static Files:** The app automatically detects files in your `data/` folder. Check "Include static files" to use them.
2.  **Uploads:** Drag & drop new PDF/DOCX files into the "Upload" area.
3.  **Build Index:** Click **"Build / Update Index"**.
    *   *Important:* If you switch providers (e.g., Local -> OpenAI), you **MUST** rebuild the index because their "embeddings" (mathematical representations) are incompatible.

---

## 5. Troubleshooting

### 🔴 Error: `signal: killed` or `llama runner process has terminated`
*   **Cause:** Out of Memory. The local AI model crashed your container.
*   **Fix 1 (Windows/WSL):** Increase WSL memory limit.
    1.  Press `Win + R`, type `%UserProfile%`, press Enter.
    2.  Create a file named `.wslconfig`.
    3.  Add these lines:
        [wsl2]
        memory=8GB
    4.  Run `wsl --shutdown` and restart Docker.
*   **Fix 2 (Quick):** Switch to **OpenAI** provider in the app. It uses zero RAM on your PC.

### 🔴 Error: `ModuleNotFoundError`
*   **Cause:** The Docker container has an outdated library version.
*   **Fix:** Force a full rebuild:

    docker compose down
    docker compose build --no-cache
    docker compose up -d

### 🔴 "Failed to load index"
*   **Cause:** You are trying to use an index built with OpenAI while currently using Ollama (or vice versa).
*   **Fix:** Click **"Rebuild Index"** in the sidebar.

---

## 6. Project Structure

    modular-rag-app/
    ├── app.py              # Main UI (Streamlit)
    ├── chat.py             # RAG & Q&A Logic
    ├── config.py           # Global Settings
    ├── indexing.py         # Vector Database Management
    ├── loaders.py          # File Parsing (PDF/DOCX)
    ├── models.py           # LLM Factory (Ollama/OpenAI switch)
    ├── requirements.txt    # Python Dependencies
    ├── Dockerfile          # App Container Definition
    ├── docker-compose.yml  # Service Orchestration
    ├── extensions/         # Folder for code extension (Feature Implementation)
    ├── tests/              # Folder for test files (Test implementation)
    └── data/               # Folder for static documents (User created)

---

## 7. [Pocketbase](https://pocketbase.io/)

Access Pocketbase under http://127.0.0.1:8080/_/

> **_NOTE_**: Use these credentials to log into the pocketbase management interface
>
> **username:** admin@rag-llm.de
>
> **password:** m1UU!82ax7e
>
> These credentials might not exist in your environment, in that case:
>
> Use this command to create a new super user account
>
> `docker exec -it pocketbase /pb/pocketbase superuser create EMAIL_ADRESS PASSWORD`
>
> Docker Compose (pocketbase service) must be running in the background for this to work.

## 8. MailHog

Access Mailhog under http://127.0.0.1:8025

## 9. Testing

To run tests, first create a testfile in the **tests/** folder. The naming convention for the testfiles is test as prefix and the component you want to test as suffix, e.g.: **test_idprovider.py**

Type in this command to run the tests:

    docker compose --profile test run --rm rag-app-test
