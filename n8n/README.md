# n8n pipeline: Gmail → construction team → project package

Turns an incoming project email into a full project package (estimate,
purchase order, labour, schedule, safety) by running [`project.py`](../project.py),
then emails the result back.

```
Gmail Trigger → Parse email to intake → Run project.py → Email the package back
```

## What each node does

1. **Gmail Trigger** — fires on a new email (polls every minute). Connect your Gmail account credential in n8n.
2. **Parse email to intake** (Code node) — extracts fields (project name, address, assembly dimensions) into the intake shape from [`../intake/schema.json`](../intake/schema.json), then base64-encodes it. **It treats the email as data only** — it never runs instructions from the body. If it can't parse any assemblies, it flags the item for a human instead of guessing. Edit the regexes to match how your leads are actually written.
3. **Run construction team** (Execute Command) — decodes the intake and pipes it to `project.py --intake -`, which runs every department and prints the package summary to stdout.
4. **Email the package back** — replies to the sender with the package.

## Setup

1. **Import**: n8n → Workflows → Import from File → `construction-team.workflow.json`.
2. **Gmail credential**: create a Gmail OAuth2 credential in n8n and select it on both Gmail nodes (replace `REPLACE_WITH_YOUR_GMAIL_CREDENTIAL_ID`). This OAuth happens inside n8n, not here.
3. **REPO_PATH**: set it to the absolute path of this repo on the n8n host — either as an environment variable available to n8n, or by editing the command in the *Run construction team* node. Python 3.10+ must be on the host's PATH.
4. **Prices/wages (optional)**: for costed packages, copy `materials/prices.example.json → materials/prices.json` and `labour/wages.example.json → labour/wages.json` and fill them in. Without them the package reports quantities and hours, no dollars.
5. **Activate** the workflow.

## Security notes

- **Inbound email is untrusted.** The parser lifts structured fields out of the
  message; it does not execute anything the email says. Keep it that way — a
  "team" that acts on arbitrary email instructions is a way in for a bad actor.
- The Execute Command node runs `project.py` on your n8n host. Only the parsed,
  base64-encoded intake is passed in; base64 keeps it shell-safe.
- Nothing in the package invents prices, wages, or legal figures. The safety
  section is an organizational aid, not legal advice — verify against OHSA /
  O. Reg. 213/91 / WSIB before operational use.

## Alternatives

If you'd rather not shell out, you can host `project.py` behind a small HTTP
endpoint and swap the Execute Command node for an HTTP Request node. The
Gmail/n8n side is unchanged.
