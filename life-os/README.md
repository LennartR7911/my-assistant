# Life OS - Personal Knowledge Management System

## Overview
Life OS is a modular Python application designed to act as your "second brain". It integrates **Super Productivity** (via GitHub Issues), your local file system (Markdown/Audio), and **Google Gemini** to automate organization, enrich tasks with context, and process raw input.

## Architecture & How It Works

The system runs as a set of background services managed by `main.py`:

### 1. Task Synchronization (The "Brain")
*   **Frontend**: You manage tasks in **Super Productivity**, which syncs with **GitHub Issues**.
*   **Backend (`task_enricher.py`)**:
    *   Runs every 60 seconds.
    *   Checks for open GitHub Issues **without** the `enriched` label.
    *   Reads `context.yaml` from your project folders.
    *   Scans recent `Logs/` for keywords.
    *   Uses **Gemini 2.0 Flash** to summarize the task, identify stakeholders, and generate 3 actionable steps.
    *   Posts a comment on the GitHub Issue and adds the label `enriched`.
    *   **Result**: When you open the task in Super Productivity, you see the AI-generated context immediately.

### 2. Daily Log Generator
*   **Script (`daily_setup.py`)**:
    *   Runs on startup.
    *   Fetches all **Prio 1 (P1)** issues from GitHub.
    *   Creates a daily markdown file in `Logs/{YYYY-MM-DD}.md`.
    *   **Template**: Includes your P1 tasks as a checklist and a section for a "Brain Dump".

### 3. Inbox Processor (The "Receptionist")
*   **Script (`input_handler.py`)**:
    *   Watches the `Inbox/` folder in real-time.
    *   **Audio (.mp3)**: Uploads to Gemini -> Transcribes & Summarizes -> Saves to `Meeting_Notes/` -> Moves original to `Archive/Audio`.
    *   **Text (.txt)**: Reads raw notes -> Extracts action items via Gemini -> Creates new GitHub Issues -> Moves original to `Archive/Raw`.

### 4. Project Scaffolder
*   **Script (`project_manager.py`)**:
    *   Run via the CLI menu.
    *   Creates a standardized folder structure: `Projects/{Client}/{Name}/` with `01_Admin`, `02_Notes`, `03_Deliverables`.
    *   Generates a `context.yaml` file for project metadata (Stakeholders, Goals) which the **Task Enricher** uses.

## Installation & Setup

### Prerequisites
*   Python 3.11+
*   A GitHub Account & Personal Access Token (Repo scope)
*   A Google Cloud Project with Gemini API enabled

### 1. Clone & Install
```bash
cd life-os
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the `life-os` directory (copy from `.env.example`):
```ini
GOOGLE_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_pat
GITHUB_REPO=owner/repo_name
KNOWLEDGE_BASE_PATH=./  # Or absolute path to your OneDrive/Docs folder
```

### 3. Run the System
```bash
python main.py
```
This will:
1.  Generate today's Daily Log (if missing).
2.  Start watching the `Inbox/` folder.
3.  Start the Task Enricher loop in the background.
4.  Show a CLI menu to create new projects.

## Usage Guide for Frontend (Super Productivity)

1.  **Connect GitHub**: In Super Productivity, add a "GitHub" integration pointing to the same repository configured in `.env`.
2.  **Create Tasks**:
    *   Create a task in Super Productivity.
    *   It syncs to GitHub as an Issue.
    *   **Wait ~60s**: The `Life OS` daemon picks it up, analyzes it using your Project Contexts, and posts a comment with an AI summary.
    *   **Sync Back**: The comment appears in Super Productivity notes/comments.
3.  **Voice Notes**:
    *   Record audio on your phone/PC.
    *   Save/Drop the `.mp3` file into the `Inbox/` folder.
    *   Life OS automatically transcribes it to `Meeting_Notes/` and archives the audio.
4.  **Quick Notes**:
    *   Write a `note.txt` in `Inbox/` with rough thoughts.
    *   Life OS extracts actionable tasks and creates GitHub Issues for you.

## Directory Structure
*   `Projects/`: Organized client/project folders with `context.yaml`.
*   `Logs/`: Daily markdown logs.
*   `Inbox/`: Drop zone for `.mp3` and `.txt`.
*   `Archive/`: Processed raw files.
*   `Meeting_Notes/`: AI summaries of audio.
