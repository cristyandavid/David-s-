# OpenClaw — Google Drive skill

Provides read access to Google Drive files from within OpenClaw.

## One-time setup

### 1. Enable the Drive API

In the Google Cloud project that OpenClaw uses:

**Via the Cloud Console:**
1. Go to **APIs & Services → Library**.
2. Search for **Google Drive API** and click **Enable**.

**Via the CLI:**
```bash
gcloud services enable drive.googleapis.com
```

### 2. Create OAuth credentials

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth client ID**.
3. Choose **Desktop app**, give it a name, then click **Create**.
4. Download the JSON file and save it to:
   ```
   /root/.openclaw/credentials/google-drive.json
   ```

### 3. Install Python dependencies

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 4. Authorize OpenClaw

Run the authentication script once; it opens a browser for the OAuth consent
screen and saves a refresh token for future runs:

```bash
python3 skills/google-drive/scripts/list_files.py
```

After authorization the token is cached at:
```
/root/.openclaw/credentials/google-drive-token.json
```

Subsequent runs use the cached token and do **not** require a browser.

## Usage

```bash
# List the 20 most-recently-modified files in your Drive
python3 skills/google-drive/scripts/list_files.py
```

## File layout

```
skills/google-drive/
├── README.md                    # this file
└── scripts/
    └── list_files.py            # OAuth flow + Drive file listing
```

## Security notes

- The credential files contain sensitive tokens. They are stored under
  `/root/.openclaw/credentials/` which should be mode `700`.
- `google-drive-token.json` should **not** be committed to version control.
  Add it to `.gitignore` if you store credentials elsewhere in the repo.
- The script requests `drive.readonly` scope only. Widen to `drive` only if
  write access is explicitly required.
