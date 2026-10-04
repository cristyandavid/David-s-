# NFC Service Log

Tap an NFC tag -> iPhone runs a shortcut -> row appears in **Home Services Log**
(service tab + `All Services`).

## One-time setup
1. Open the sheet > Extensions > Apps Script. Paste `apps-script/Code.gs`.
2. Project Settings > Script properties > add `TAP_TOKEN` = a long random string.
3. Deploy > New deployment > Web app > Execute as **Me**, access **Anyone**. Copy the `/exec` URL.
4. On a Mac: `./sign.sh`, AirDrop `shortcuts/signed/*.shortcut` to the iPhone.
   When importing, paste `<exec URL>?token=<TAP_TOKEN>` at the prompt.
5. iPhone Shortcuts > Automation > New > NFC > scan a tag > Run Shortcut `Log <Service>` > turn off "Ask Before Running".
   One tag per service.

`python3 generate_shortcuts.py` regenerates the unsigned shortcuts.
