# Set up the church's shared Firebase archive

The app requires Firebase sign-in and approved membership before showing the editor. Printing and downloads automatically archive the editable sheet first. An internet connection, Firebase project and approved accounts are required. Use one project for one church/team: every approved member can read and publish all archived notices in that project.

Use the **Spark** plan for the initial setup. Do not enable billing, Cloud Functions, Cloud Storage or paid extensions for this feature. Firebase's current free quotas and email limits still apply: https://firebase.google.com/pricing . Public sign-in pages do not make the private archive public; the database rules enforce membership.

## 1. Create the project and web app

1. Open https://console.firebase.google.com/ using the Google account which should administer the church archive.
2. Create a project. Google Analytics is optional and is not used by this app.
3. In **Project settings → General**, add a **Web app** (`</>`). Firebase Hosting is not required: GitHub Pages can continue hosting the notice builder.
4. Find the web app's `firebaseConfig`. You need only its **projectId** and **apiKey**. These are public connection settings, not administrator credentials. Never copy a service-account JSON file or private key into the app, GitHub, chat or a draft.
5. Under **Authentication → Sign-in method**, enable **Email/Password**. The app does not use Google sign-in or SMS.
6. Under **Authentication → Settings → Authorized domains**, add the deployed site's hostname (for example `jackwolf-alt.github.io`). Configure password-reset email templates and their action URL through Firebase's default handler, rather than pointing password-reset links directly to `index.html`.

## 2. Create the database and deploy the access rules

1. Open **Firestore Database**, create the default database in **production mode**, and choose the appropriate region for the church's data (for example a UK or European region). If asked to choose an edition, use Standard.
2. In its **Rules** tab, replace the rules with the complete contents of [firestore.rules](firestore.rules), then **Publish**. Do not use test-mode rules or a rule allowing every signed-in account to read/write.
3. Alternatively, an administrator can deploy only the rules using the Firebase CLI from the repository root:

   ```sh
   firebase login
   firebase deploy --only firestore:rules --project YOUR_PROJECT_ID
   ```

The supplied rules allow approved members to read the archive and create immutable snapshots. They prohibit client-side account approval, collection-wide member listings, editing/deleting published snapshots, unexpected document fields and anonymous access. Administrators can remove incorrect or sensitive records in the Firebase console. Membership approval is required even if someone registers an account directly through Firebase's public authentication API.

## 3. Add and approve users

For each church user:

1. In **Authentication → Users**, choose **Add user**, enter their email and a unique temporary password. Do not use a password shared by the whole team.
2. Copy that user's **UID**.
3. In Firestore's **Data** tab, create a collection named `members`. Create a document whose **document ID is exactly that UID**, with a boolean field **enabled = true**. Use the console, not the notice builder, for this step.
4. Give the user the notice-builder link and their public archive connection details. On the sign-in screen, they can enter their email and choose **Reset password** to set their own password using the Firebase email, then sign in. Configure Firebase's email templates before inviting the wider team.
5. To revoke access, set their member document's `enabled` field to `false` or delete the member document. This blocks subsequent archive reads/writes immediately, even while an existing Firebase token is still valid. Disable their Authentication account too if appropriate. Previously downloaded or copied data cannot be recalled.

## 4. Connect the notice builder

On the first sign-in screen, under **Connect the church archive**, enter the project ID and web API key, then **Save connection**. Each browser remembers only these public connection details. Passwords and login tokens are never saved to localStorage or JSON drafts. Sessions last only in the current page: reload or close it to sign out, or choose **Sign out** explicitly.

The deployed app is already preconfigured for the church project. For another deployment, fill in `FIREBASE_CONFIG` near the bottom of `index.html` with only the public `projectId` and `apiKey`. This removes the need to enter them on each browser. An existing browser's saved connection takes precedence; use **Save connection** to switch it. API keys identify the project; security comes from Authentication and Firestore rules. Set appropriate API restrictions for Identity Toolkit and Token Service and website restrictions for the deployed app, then test sign-in, password reset and token refresh.

For restricted cloud task networking, allow these HTTPS domains when testing against a live project:

- `identitytoolkit.googleapis.com` — sign-in and password reset.
- `securetoken.googleapis.com` — refreshing the current page's login token.
- `firestore.googleapis.com` — approved archive reads and publishing.

No secret credential needs to be entered into the cloud environment for browser users. Each person signs in on the website.

## 5. Verify with two accounts before real notices

1. Sign in as an approved member. Print or download a synthetic sheet with a Sunday date. Confirm the saved entry can reopen its rota and size settings.
2. Sign in as a second approved member in another browser. Refresh, search the title, expand the saved week, and add one notice to the current sheet. Check its wording/date before printing.
3. Try a user without a `members/UID` document and a signed-out browser. Neither should read or publish archive documents.
4. Disable a member and verify subsequent reads and writes are denied. Test password reset from its actual email and sign-in again with the new password.
5. Export a local editable draft. It must contain no login credentials or Firebase session tokens.

**What is shared:** the reviewed sheet's archive title, Sunday date, church name, website, usual service times, services, notices, rota and size settings, plus the publishing UID and server save timestamp. The pasted source email and uploaded logo are excluded, and passwords/tokens are never stored in the archive. The sign-in screen explains that printing, PDF download and editable-draft download save the sheet automatically; no extra confirmation is required on each output. **Save sheet now** also saves without output. A missing title defaults to the Sunday date.

Changed sheets create new immutable snapshots; retries and unchanged exports from the same account reuse their existing snapshot. Saving must succeed before output starts. A failed save leaves the local draft intact and stops printing/download. Closing a print dialog without printing still leaves the snapshot in the archive. Direct browser Ctrl/Cmd+P only prints a sheet if the unchanged version has already been saved during that page session; otherwise it prints a reminder to use the app's Print button. The app cannot detect whether a physical printer actually printed.

To recall a specific notice, search the archive, expand a saved week, and choose **Add notice to this week**. It appends that one item without replacing other notices or rota entries; services can also be recalled individually. **Open saved sheet** restores the whole sheet's content, rota and layout settings after confirmation, clears the pasted email and keeps the device's current logo. Stored PDFs and original logos are not archived. Earlier services/notices-only records still support individual recall but do not offer full-sheet restoration. Search covers the loaded records (50 per page); **Load older weeks** expands the search. Repeat instructions in emails show a reminder to search, not an automatic guess. Back up important records: free-plan quotas are not a backup service.

The sign-in gate controls the app's normal user interface; this is still a public static site, so its HTML and JavaScript can be downloaded. Firebase rules enforce access to shared data. Existing local drafts belong to that browser; signing out hides them but does not delete them. Protect shared computers appropriately. No database rules change is required to upgrade from the previous services/notices-only archive: the new sheet snapshot uses the existing validated `content` field and size limit.

## Development validation

`python3 tests/archive_smoke.py` tests the browser UI against intercepted synthetic Firebase REST responses. It does not prove live credentials or production rules are working.

The rules tests exercise the real Firestore emulator. Install optional development tools outside the app (no runtime library/build is required):

```sh
npm install --prefix /tmp/notice-firebase-tests firebase-tools @firebase/rules-unit-testing firebase
NOTICE_FIREBASE_TEST_MODULES=/tmp/notice-firebase-tests/node_modules \
  /tmp/notice-firebase-tests/node_modules/.bin/firebase emulators:exec \
  --only firestore --project demo-high-church 'node tests/firestore_rules.cjs'
```

The Firebase CLI needs Java 21+ and may download its emulator on first use. `demo-high-church` is a local demo project; never run emulator tests against the live church project. Run the browser regressions with `python3 tests/browser_smoke.py` too.
