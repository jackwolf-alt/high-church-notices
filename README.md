# Churchpress

**Your church notices, ready for Sunday.**

A static, browser-only notice-sheet maker. Paste an email, review the extracted services and notices, and export two matching A5 notices on one landscape A4 PDF. A Firebase-approved account is required before the editor opens. Email formatting and PDF rendering run in your browser without a build system; printing and downloads first save the editable sheet to the shared archive.

## Publish it as a permanent web app with GitHub Pages

1. Create a free GitHub account if you do not already have one.
2. Create a **public** repository called `high-church-notices` (or another name). Leave it empty.
3. Unzip this package. In the GitHub repository, choose **Add file > Upload files**, select the app files from the unzipped folder (`index.html`, `README.md`, `AGENTS.md`) plus the `.nojekyll` file if present, and **Commit changes**. `index.html` must be at the top level of the repository — not inside a subfolder.
4. Under **Settings > Pages**, set **Source** to **Deploy from a branch**, **Branch** to `main`, **Folder** to `/(root)`, and **Save**.
5. Once published, the address should be `https://YOUR-USERNAME.github.io/high-church-notices/` (using your actual GitHub username and repository name).
6. Bookmark it, or in Safari on a Mac choose **File > Add to Dock**.

**Important:** GitHub Pages sites are public, and on a free GitHub plan the repository will also be public. The package contains no real minister email or named rota entries; do not commit weekly email text, drafts, or private church records to GitHub. The live form and PDF export work in the browser. The Firebase archive uses approved-user access rules even when the static website is public. Never put private archive data or administrator credentials in GitHub.

## Sign-in, automatic saving and recalling notices

Select your church on the first screen and sign in with an account approved by that church's administrator. The editor, previews, print controls and local drafts stay hidden until both login and membership checks succeed. Signing out or reloading returns to the sign-in screen. Firebase account setup and the same membership rules are described in [Firebase setup](firebase/SETUP.md).

**Print**, **Download PDF** and **Download editable draft** automatically save the current editable sheet before producing output. The snapshot includes services, notices, the rota, church name, footer website, usual service times and size settings. It excludes the pasted email and uploaded logo. PDF files themselves are not stored: archived sheets can be reopened and rendered again, using the logo currently on that device. An optional archive title defaults to the Sunday date.

Unchanged content from the same account is saved once, including after reloads or retries. Changes to the sheet or archive title create a new immutable snapshot. An internet connection and archive access are required for output; if saving fails, no print dialog or download is started, and your local draft is kept. The save happens before a print dialog opens, so cancelling printing leaves the snapshot archived. Browser Ctrl/Cmd+P cannot wait for a cloud save: an unsaved revision prints a reminder to use the app's Print button instead of the sheet.

To recall a specific notice, open **Shared notice archive**, search for a phrase or topic, expand the matching week, and choose **Add notice to this week**. It appends only that notice, leaving other content and the rota intact. Services work the same way. Search covers the loaded weeks, newest publications first; use **Load older weeks** to search further back. **Open saved sheet** is a separate action which restores a full sheet, including its rota and sizes, after confirmation. It clears the current pasted email and keeps the current device's logo. Older services/notices-only archive records remain searchable and reusable.

Run `python3 tests/archive_smoke.py` for the intercepted Firebase browser integration and `python3 tests/browser_smoke.py` for rendering regressions with simulated sign-in. See the setup guide for Firestore emulator tests and the two-user live acceptance check.

## Interface and church branding

The Churchpress interface uses the supplied transparent logo, navy `#06265E`, blue `#087CFA`, paper blue `#EDF5FF`, ink `#182338` and slate `#53627A`. Manrope is embedded for the interface, browser print and downloaded PDFs. The default Large body is 11 pt at 110% overall size; smaller presets remain available for busy weeks. The landscape A4/two-A5 geometry is preserved. **Prepare**, **Edit**, **Print & save** and **Archive** tabs group related controls in a wider editor. The always-visible preview offers **Fit to panel** and manual zoom choices. These screen zoom choices do not alter print size.

The full Churchpress wordmark appears on white in the app header and sign-in screen, in its original proportions and colours. It was extracted losslessly, including transparency, from the supplied brand guide. The church's own name/logo and weekly details lead on the printed sheet; no product logo is added to the notice sheet. A configured church logo supplies the default printed logo, and a locally uploaded logo can replace it for that browser.

Each customer church uses its own Firebase project/database and approved user list. The public church directory is maintained in `CHURCHES` in `index.html`; onboarding steps and live separation checks are in [Firebase setup](firebase/SETUP.md). Selecting another church signs out and switches to separate local draft storage. Existing local drafts migrate only to Stornoway. All approved users of a church can read its earlier archived notices.

`python3 tests/brand_smoke.py` checks the brand palette, full logo, Manrope, 11 pt default print body, action contrast and branded output names. `python3 tests/interface_smoke.py` verifies church selection, legacy draft migration, separate draft/logo contexts, approval per project, request routing, keyboard tabs, fonts and responsive preview fit using synthetic Firebase responses.

## Move your saved draft from the earlier downloaded HTML file

1. Open your current programme and choose **Download editable draft** (`.json`).
2. Open the newly published website and choose **Open saved draft**.
3. Check all the information before printing. Data is browser-specific: the new website does not automatically inherit browser storage from the old file.

## Updating with Codex

1. Open Codex and connect your GitHub account and the `high-church-notices` repository.
2. Describe the change you want, e.g., “Increase the print preview heading sizes, while preserving the exact two-A5-on-A4 layout. Test PDF output and the service parser.”
3. Review/test the update. Merge its pull request into `main` when you are happy; GitHub Pages will republish it.

## Local draft backups and connectivity

JSON drafts remain browser-compatible with earlier versions and contain no login credentials. Source email text and uploaded logos stay in local drafts, not in the shared archive. Browser autosave keeps your current work if an archive request fails. A network connection is now required to sign in, print or download; there is no offline login bypass. Keep existing JSON backups before changing browser, device or website address.

## Adjust the sheet size

In **Print settings**, use **Overall sheet size** to enlarge or shrink the complete notice sheet (70–150%). It starts at 110%, preserving the previous 10% increase. Under **Adjust individual sections**, independently resize the church header/date, services, other notices, rota and website footer. Section percentages combine with the overall percentage; for example, 120% overall and 125% services make the services 150% of their base size. **Reset sizes** returns the overall size to 110% and every section to 100%.

These controls affect the live preview, browser print and downloaded PDF. The paper remains landscape A4 with two matching A5 copies; text reflows within the columns. Preview zoom only affects the view on screen. The existing Large/Standard/Compact text presets still work. If you see **Too much text** or an export warning, reduce sizes or shorten/move notices before printing. PDF export clips overflowing columns above the footer and warns; it does not add extra pages.

Sizes are kept in browser autosave and editable JSON drafts. Older drafts without size settings open with the defaults, and notice content stays editable. Manrope is embedded in `index.html`, including Latin characters and Gaelic accents, so rendering needs no external font service. Sign-in and archiving still require an internet connection. Manrope is distributed under the SIL Open Font License; attribution and the full licence are included in the HTML source. Source: [Google Fonts / Manrope](https://github.com/google/fonts/tree/main/ofl/manrope).

Branding changes can reflow older sheets. Existing draft and archive data, size choices and church-specific browser storage are preserved; review the preview and overflow warnings before printing an older sheet. Downloads are named `Churchpress-YYYY-MM-DD.pdf` and `Churchpress-YYYY-MM-DD-draft.json`. The machine-readable legacy JSON format identifier and storage keys stay unchanged so older drafts continue to open.

## Browser regression checks

The app itself has no dependencies or build step. Optional development checks use Python 3, Playwright and pypdf:

```sh
python3 -m pip install playwright pypdf
# If Chromium is not already installed:
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

The checks start their own temporary local server and use the system `chromium` when available (or `CHROMIUM_PATH`), otherwise Playwright's Chromium. They exercise section/overall scaling in PDF output, reset, autosave, current and legacy JSON drafts, overflow warnings, print dimensions, matching canvas halves, embedded Manrope, mobile controls and blocked signed-out/offline access. The browser checks intercept Firebase calls with synthetic responses; they do not touch the live project. Synthetic drafts and PDFs are written only to a temporary directory. Signed-out native printing is checked to ensure it does not expose the hidden sheet.

Known existing parser defect: the built-in three-service sample currently creates five entries, including two empty Sunday duplicates, both with and without a Services heading. The checks record that existing behaviour; always review extracted services and notices before printing.

## Test cases for any new version

- Paste emails with a `Services` heading and emails without one.
- Recognise AM/PM services, weekday meetings and varied date formats.
- Manually add/edit/reorder services and announcements.
- Keep the rota after formatting a new email.
- Export both the two-copy A4 PDF and the editable JSON draft.
- Check nothing overflows the printable A5 halves, especially on busy weeks.
