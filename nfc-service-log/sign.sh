#!/bin/bash
# Run on a Mac. Signs every shortcut in ./shortcuts for install on iPhone.
set -e
cd "$(dirname "$0")/shortcuts"
mkdir -p signed
for f in *.shortcut; do
  shortcuts sign --mode people-who-know-me --input "$f" --output "signed/$f"
done
echo "Signed files in $(pwd)/signed - AirDrop them to your iPhone."
