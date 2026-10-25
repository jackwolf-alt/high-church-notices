# Publish Churchpress at dashboard.churchpress.co.uk

Everything here runs in your browser: nothing needs installing on your Mac. The GitHub workflow publishes the static app to the existing **high-church-notices** Firebase project. Firebase Authentication and the archive stay in that project; no sheet styling or database rules change. Static Hosting supports Firebase's Spark plan within its free quotas; this setup does not require enabling billing.

## 1. Merge the Hosting pull request

Merge this change into `main` in GitHub. Until the two variables below are configured, deployment skips safely. It does not interrupt your existing GitHub Pages site.

## 2. Connect GitHub to Firebase using Google Cloud Shell

Open [Google Cloud Shell](https://shell.cloud.google.com/?project=high-church-notices) and sign in with the Google account that owns your Firebase project. If asked to authorise Cloud Shell, accept. This is Google's browser terminal, not the Terminal app on your Mac.

Paste these commands, one line at a time:

```sh
git clone https://github.com/jackwolf-alt/high-church-notices.git
cd high-church-notices
bash scripts/setup-firebase-github.sh
```

If you already cloned it in Cloud Shell, return to that folder and run `git pull --ff-only` instead of cloning again. You must be on the merged `main` branch.

The script enables the required APIs, creates a default static Hosting site if needed, and sets up a dedicated deploy account with Hosting administration and service-usage permission. GitHub obtains temporary credentials via Workload Identity Federation: no private key or permanent Firebase token is generated. Trust is restricted to this repository's immutable IDs, this deployment workflow, and `main` push/manual runs. Pull requests cannot use it. The script can be rerun after a partial failure.

At the end it prints two names and values. In GitHub open:

[Repository → Settings → Secrets and variables → Actions → Variables](https://github.com/jackwolf-alt/high-church-notices/settings/variables/actions)

Choose **New repository variable** for each:

| Name | Value |
| --- | --- |
| `FIREBASE_WORKLOAD_IDENTITY_PROVIDER` | The full `projects/…/locations/global/workloadIdentityPools/churchpress-github/providers/github` value printed by the script |
| `FIREBASE_DEPLOY_SERVICE_ACCOUNT` | `churchpress-hosting@high-church-notices.iam.gserviceaccount.com` |

These identifiers are not secrets. Do not upload Google service-account keys or paste passwords into GitHub or chat. This script is specific to this repository and Firebase project; changing the repository, owner or workflow filename requires updating the trust configuration.

## 3. Publish the first version

Allow a few minutes for Google's permissions to propagate. Open:

[GitHub → Actions → Deploy Churchpress to Firebase Hosting](https://github.com/jackwolf-alt/high-church-notices/actions/workflows/firebase-hosting.yml)

Choose **Run workflow**, select **main**, and run it. After a successful run, open Firebase Console → **Hosting** and follow the site's `web.app` link. Sign in and check the app before connecting the domain. Use Firebase **Hosting**, not **App Hosting**; this app has no backend build to provision.

Future merges changing the app, Hosting configuration or workflow deploy automatically. Documentation-only changes do not trigger a deployment. You can always run it manually. The deploy command uses `--only hosting`: it does not deploy Firestore rules, alter archive records or create user accounts. Only `index.html` is staged for upload; repository documents, test files and credentials are excluded.

## 4. Connect the Fasthosts subdomain

1. In Firebase **Hosting**, choose **Add custom domain** and enter **dashboard.churchpress.co.uk**. Choose the option to serve the app there, rather than redirect it elsewhere.
2. Keep Firebase's DNS instructions open. Sign in to Fasthosts, select **churchpress.co.uk**, and open its DNS settings.
3. Add exactly the records Firebase supplies. For a record for `dashboard.churchpress.co.uk`, Fasthosts will normally want **dashboard** in a relative hostname/name field. For verification records, copy Firebase's requested hostname and value; do not assume they use the same name. If the field wants a full domain, enter the full hostname. Never append `churchpress.co.uk` twice.
4. If an existing record uses the same **dashboard** hostname and conflicts, replace that record as Firebase directs. Leave the main domain, `www`, MX/email and unrelated records alone.
5. Return to Firebase and complete verification. DNS propagation and HTTPS certificate provisioning can take up to 24 hours. Wait until Firebase reports the domain connected before sharing the address.
6. In **Firebase Authentication → Settings → Authorised domains**, add **dashboard.churchpress.co.uk**. Also allow the site's `web.app` hostname if you use that for testing. If you restricted the public Firebase API key by website referrer, allow the new hostname for Identity Toolkit and Token Service too. Repeat the domain configuration in each customer church's Firebase project as you onboard it.
7. Visit **https://dashboard.churchpress.co.uk**, sign in, open the archive and test a synthetic notice/PDF. Check password reset as well.

Your accounts and shared archive remain available because the Firebase project is unchanged. Browser autosaved drafts and uploaded church logos are tied to the old website address and do not transfer automatically. Before moving, download an editable draft on the old site, then import it on the new address. Upload your church logo again if needed. Downloading a draft also archives the reviewed sheet under the app's existing behaviour; its pasted email and logo stay only in that local JSON file. Keep that backup private.

Keep the old site available until you have transferred drafts and tested the new address. DNS remains managed at Fasthosts; there is no need to move the domain or its nameservers to Google.

## If something fails

- **Skipped deployment:** confirm both entries are repository **variables**, not secrets, and run on `main` after merging.
- **New deploy account “does not exist”:** Google IAM can briefly lag behind account creation. The script retries this automatically. If it still stops, wait a minute and run `bash scripts/setup-firebase-github.sh` again from the same Cloud Shell folder. Keep the existing account; the script resumes safely.
- **Cloud Shell permission/API error:** use the project owner account, check the project shown by the script, allow a few minutes and rerun. If an organisation blocks Workload Identity Federation, its administrator must permit it.
- **GitHub authentication/403 error:** check the printed variable values exactly. Rerun setup, wait a few minutes and retry the workflow. The workflow name/path and repository IDs must match the script.
- **Site name already taken:** create a default Hosting site through Firebase Console and rerun setup. Do not change the church's Firebase database project to solve a website naming issue.
- **Need to undo a release:** Firebase Console → Hosting → release history lets you roll back the website. Revert the corresponding code change in GitHub too so a later deployment keeps the correction. Archive records are unaffected by a Hosting rollback.

## Public website at the main domain

The advertising site uses a separate Hosting site and configuration. See [Public website setup](PUBLIC-SITE.md). Keep `dashboard.churchpress.co.uk` attached to the existing default site when connecting `churchpress.co.uk` to the new public site.

## Local development checks (optional)

Developers can run `bash scripts/prepare-hosting.sh` and serve `dist` using the Firebase Hosting emulator. This is not needed on your laptop for the browser-only setup above. The existing Firestore emulator configuration and browser smoke tests remain available.
