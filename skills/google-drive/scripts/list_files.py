"""
OpenClaw — Google Drive integration: list files.

Usage:
    python3 skills/google-drive/scripts/list_files.py

Prerequisites:
    1. Google Drive API enabled in your Google Cloud project.
    2. OAuth client credentials (desktop app) saved to:
           /root/.openclaw/credentials/google-drive.json
    3. Dependencies installed:
           pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

On first run the script opens a browser for OAuth consent and writes a token
to /root/.openclaw/credentials/google-drive-token.json for subsequent runs.
"""

import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Read-only scope — expand to drive if writes are needed.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

CREDENTIALS_DIR = Path("/root/.openclaw/credentials")
CLIENT_SECRETS = CREDENTIALS_DIR / "google-drive.json"
TOKEN_FILE = CREDENTIALS_DIR / "google-drive-token.json"


def _load_or_refresh_creds() -> Credentials:
    """Return valid credentials, running the OAuth flow if necessary."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {CLIENT_SECRETS}\n"
                    "Download OAuth client credentials (desktop app) from the\n"
                    "Google Cloud Console and save them to that path."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS), SCOPES
            )
            creds = flow.run_local_server(port=0)

        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def list_drive_files(page_size: int = 20) -> list[dict]:
    """Return up to *page_size* files from the authenticated user's Drive."""
    creds = _load_or_refresh_creds()
    service = build("drive", "v3", credentials=creds)

    results = (
        service.files()
        .list(
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )
    return results.get("files", [])


def main() -> None:
    files = list_drive_files()
    if not files:
        print("No files found.")
        return

    print(f"{'ID':<44} {'Name'}")
    print("-" * 80)
    for f in files:
        print(f"{f['id']:<44} {f['name']}")


if __name__ == "__main__":
    main()
