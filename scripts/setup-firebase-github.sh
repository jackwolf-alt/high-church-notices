#!/usr/bin/env bash
# Run once in Google Cloud Shell as the Firebase project administrator.
# No service-account key or Firebase login token is created.
set -euo pipefail

project_id='high-church-notices'
pool_id='churchpress-github'
provider_id='github'
service_account_id='churchpress-hosting'
repository_id='1432657428'
service_account="${service_account_id}@${project_id}.iam.gserviceaccount.com"

# New IAM resources can exist in one Google service before another sees them.
# Retry propagation/concurrent-policy errors, but stop on permission/config errors.
retry_iam() {
  local attempt error_file status
  error_file=$(mktemp)
  for attempt in 1 2 3 4 5 6; do
    if "$@" 2>"$error_file"; then
      cat "$error_file" >&2
      rm -f "$error_file"
      return 0
    else
      status=$?
    fi
    cat "$error_file" >&2
    if (( attempt == 6 )) || ! grep -Eqi 'does not exist|not found|NOT_FOUND|ABORTED|concurrent policy' "$error_file"; then
      rm -f "$error_file"
      return "$status"
    fi
    printf 'Waiting 10 seconds for Google IAM to propagate (attempt %s of 6).\n' "$attempt" >&2
    sleep 10
  done
}

printf 'Configuring GitHub deployment for Firebase project %s.\n' "$project_id"
gcloud projects describe "$project_id" --format='table(projectId,name,projectNumber)'
gcloud services enable \
  firebase.googleapis.com firebasehosting.googleapis.com \
  iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com \
  cloudresourcemanager.googleapis.com serviceusage.googleapis.com \
  --project="$project_id"
project_number=$(gcloud projects describe "$project_id" --format='value(projectNumber)')

# Provision the default static Hosting site if this project has never hosted.
# The access token stays in this process and is never printed or written to disk.
python3 - "$project_id" <<'PYTHON'
import json
import subprocess
import sys
import urllib.error
import urllib.request

project = sys.argv[1]
token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
base = f'https://firebasehosting.googleapis.com/v1beta1/projects/{project}/sites'

def request(url, data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit(f'Hosting setup failed (HTTP {error.code}). Check project permissions, '
                         'allow a few minutes after enabling APIs, then rerun. '
                         'If the site name is taken, create a default site in Firebase Hosting first.')

sites = request(base).get('sites', [])
if not any(site.get('type') == 'DEFAULT_SITE' for site in sites):
    site = request(base + f'?siteId={project}', b'{}')
    print('Created Hosting site:', site['name'])
else:
    print('Default Hosting site already exists.')
PYTHON

if ! gcloud iam service-accounts describe "$service_account" --project="$project_id" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$service_account_id" \
    --display-name='Churchpress Hosting deployer' --project="$project_id"
fi
# Hosting deployment only; this account receives no archive/Auth administration role.
for role in roles/firebasehosting.admin roles/serviceusage.serviceUsageConsumer; do
  retry_iam gcloud projects add-iam-policy-binding "$project_id" \
    --member="serviceAccount:${service_account}" --role="$role" --condition=None --quiet >/dev/null
done

if ! gcloud iam workload-identity-pools describe "$pool_id" \
  --location=global --project="$project_id" >/dev/null 2>&1; then
  retry_iam gcloud iam workload-identity-pools create "$pool_id" --location=global \
    --display-name='Churchpress GitHub deployments' --project="$project_id"
fi

# Immutable GitHub IDs stop a renamed/deleted repository being impersonated.
# Restrict credentials to this workflow on main, on push or manual dispatch.
condition="assertion.repository_id == '${repository_id}' && assertion.repository_owner_id == '340526538' && assertion.ref == 'refs/heads/main' && assertion.workflow_ref == 'jackwolf-alt/high-church-notices/.github/workflows/firebase-hosting.yml@refs/heads/main' && (assertion.event_name == 'push' || assertion.event_name == 'workflow_dispatch')"
provider_command=create-oidc
if gcloud iam workload-identity-pools providers describe "$provider_id" \
  --workload-identity-pool="$pool_id" --location=global --project="$project_id" >/dev/null 2>&1; then
  provider_command=update-oidc
fi
retry_iam gcloud iam workload-identity-pools providers "$provider_command" "$provider_id" \
  --workload-identity-pool="$pool_id" --location=global --project="$project_id" \
  --issuer-uri='https://token.actions.githubusercontent.com' \
  --attribute-mapping='google.subject=assertion.sub,attribute.repository_id=assertion.repository_id' \
  --attribute-condition="$condition"

retry_iam gcloud iam service-accounts add-iam-policy-binding "$service_account" \
  --project="$project_id" --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${project_number}/locations/global/workloadIdentityPools/${pool_id}/attribute.repository_id/${repository_id}" \
  --quiet >/dev/null

printf '\nSetup complete. Add these GitHub Actions repository VARIABLES (not secrets):\n\n'
printf 'FIREBASE_WORKLOAD_IDENTITY_PROVIDER\nprojects/%s/locations/global/workloadIdentityPools/%s/providers/%s\n\n' "$project_number" "$pool_id" "$provider_id"
printf 'FIREBASE_DEPLOY_SERVICE_ACCOUNT\n%s\n\n' "$service_account"
printf 'Allow a few minutes for permissions to propagate, then run the deployment workflow on main.\n'
