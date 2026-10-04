# Build the shortcut by hand (no Mac, no signing)

Do this once per service (Garbage, Coffee Mug, Coffee Machine, Laundry, Toothbrush).

1. Shortcuts app > **+** > name it `Log Laundry` (change per service).
2. **Add Action** > search **Get Contents of URL**.
3. URL: `<your Apps Script /exec URL>?token=<your TAP_TOKEN>`
4. Tap the arrow to expand: **Method = POST**, **Request Body = JSON**.
5. **Add new field** > **Text**: key `service`, value `Laundry` (exact tab name).
6. **Add new field** > **Text**: key `source`, value `NFC`.
7. **Add Action** > **Show Notification**. Title `Laundry`; body: tap the field and pick the variable **Contents of URL**.
8. Done. Run it once: you should get a "Laundry logged ..." notification and new rows in the Sheet and Notion.

Tip: finish one, then **Duplicate** it and change only the name and the `service` value for the rest.
Then do step 7 of README.md (NFC automations).
