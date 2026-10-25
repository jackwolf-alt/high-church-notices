#!/usr/bin/env bash
# Run in Google Cloud Shell after merging the public website PR.
# Reuses the existing Hosting deployer and GitHub OIDC trust. No keys are needed.
set -euo pipefail
python3 - <<'PYTHON'
import json
import subprocess
import urllib.error
import urllib.request

project = 'high-church-notices'
site = 'churchpress-public-833739660900'
token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
base = f'https://firebasehosting.googleapis.com/v1beta1/projects/{project}/sites'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
try:
    try:
        with urllib.request.urlopen(urllib.request.Request(base + '/' + site, headers=headers), timeout=60) as response:
            existing = json.load(response)
            print('Public Hosting site already exists:', existing['name'])
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        req = urllib.request.Request(base + '?siteId=' + site, data=b'{}', headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            created = json.load(response)
            print('Created separate public Hosting site:', created['name'])
except urllib.error.HTTPError as error:
    raise SystemExit(f'Public Hosting setup failed (HTTP {error.code}). Check the project owner account and try again. No existing site was replaced.')
print('\nNext: add GitHub Actions repository variable FIREBASE_PUBLIC_SITE_ENABLED with value true.')
print('Then run the existing deployment workflow on main.')
print(f'Test https://{site}.web.app before adding churchpress.co.uk to THIS new site in Firebase Hosting.')
print('Keep dashboard.churchpress.co.uk attached to the existing high-church-notices site.')
PYTHON
