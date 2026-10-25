# Stornoway High Church Notice Builder

A static, browser-only notice-sheet maker. Paste an email, review the extracted services and notices, and export two matching A5 notices on one landscape A4 PDF. Editing, email formatting and PDF export run locally without a build system. An optional Firebase shared archive adds approved-user logins and explicit publishing; local use needs no database or API key.

## Publish it as a permanent web app with GitHub Pages

1. Create a free GitHub account if you do not already have one.
2. Create a **public** repository called `high-church-notices` (or another name). Leave it empty.
3. Unzip this package. In the GitHub repository, choose **Add file > Upload files**, select the three files from the unzipped folder (`index.html`, `README.md`, `AGENTS.md`) plus the `.nojekyll` file if visible, and **Commit changes**. `index.html` must be at the top level of the repository — not inside a subfolder.
4. Under **Settings > Pages**, set **Source** to **Deploy from a branch**, **Branch** to `main`, **Folder** to `/(root)`, and **Save**.
5. Once published, the address should be `https://YOUR-USERNAME.github.io/high-church-notices/` (using your actual GitHub username and repository name).
6. Bookmark it, or in Safari on a Mac choose **File > Add to Dock**.

**Important:** GitHub Pages sites are public, and on a free GitHub plan the repository will also be public. The package contains no real minister email or named rota entries; do not commit weekly email text, drafts, or private church records to GitHub. The live form and PDF export work in the browser. The optional Firebase archive uses approved-user access rules even when the static website is public. Never put private archive data or administrator credentials in GitHub.

## Shared archive and logins

See [Firebase setup](firebase/SETUP.md) to create a Spark-plan project, enable email/password accounts, deploy the private database rules and approve church users. The website itself can stay on GitHub Pages. Firebase is optional: it is contacted only when you use the archive controls, and local PDF/draft workflows continue offline.

Sign in under **Shared notice archive**, give the current week a title, and choose **Publish services & notices**. Only reviewed services/notices are shared, after confirmation; the pasted email, rota, logo and print settings stay local. Search the loaded weeks, load older ones as needed, expand a saved week and add individual notices/services to the current sheet. Always review their dates and wording. A minister's “repeat last notice” instruction shows an archive-search reminder rather than guessing.

Run `python3 tests/archive_smoke.py` for the mocked Firebase browser integration. See the setup guide for emulator security tests and the required two-user live acceptance check.

## Move your saved draft from the earlier downloaded HTML file

1. Open your current programme and choose **Download editable draft** (`.json`).
2. Open the newly published website and choose **Open saved draft**.
3. Check all the information before printing. Data is browser-specific: the new website does not automatically inherit browser storage from the old file.

## Updating with Codex

1. Open Codex and connect your GitHub account and the `high-church-notices` repository.
2. Describe the change you want, e.g., “Increase the print preview heading sizes, while preserving the exact two-A5-on-A4 layout. Test PDF output and the service parser.”
3. Review/test the update. Merge its pull request into `main` when you are happy; GitHub Pages will republish it.

## Using without internet

The `index.html` file also runs directly on your computer when opened in a browser, offline. Online hosting is optional and is mainly for a stable address and easier updates. Do not rely on browser autosave as your only backup; export the editable draft (`.json`) before making major changes.

## Adjust the sheet size

In **Print settings**, use **Overall sheet size** to enlarge or shrink the complete notice sheet (70–150%). It starts at 110%, preserving the previous 10% increase. Under **Adjust individual sections**, independently resize the church header/date, services, other notices, rota and website footer. Section percentages combine with the overall percentage; for example, 120% overall and 125% services make the services 150% of their base size. **Reset sizes** returns the overall size to 110% and every section to 100%.

These controls affect the live preview, browser print and downloaded PDF. The paper remains landscape A4 with two matching A5 copies; text reflows within the columns. Preview zoom only affects the view on screen. The existing Large/Standard/Compact text presets still work. If you see **Too much text** or an export warning, reduce sizes or shorten/move notices before printing. PDF export clips overflowing columns above the footer and warns; it does not add extra pages.

Sizes are kept in browser autosave and editable JSON drafts. Older drafts without size settings open with the defaults, and notice content stays editable. Montserrat is embedded in `index.html`, including Latin characters and Gaelic accents, so the sheet and PDF work offline without a font service. Montserrat is distributed under the SIL Open Font License; attribution and the full licence are included in the HTML source. Source: [Google Fonts / Montserrat](https://github.com/google/fonts/tree/main/ofl/montserrat).

## Browser regression checks

The app itself has no dependencies or build step. Optional development checks use Python 3, Playwright and pypdf:

```sh
python3 -m pip install playwright pypdf
# If Chromium is not already installed:
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

The checks start their own temporary local server and use the system `chromium` when available (or `CHROMIUM_PATH`), otherwise Playwright's Chromium. They exercise section/overall scaling in PDF output, reset, autosave, current and legacy JSON drafts, overflow warnings, print dimensions, matching canvas halves, embedded Montserrat, mobile controls and offline file export. Synthetic drafts and PDFs are written only to a temporary directory. If managed browser policy blocks `file://` navigation, that check is reported as skipped and the same HTML is exercised in an offline document instead.

Known existing parser defect: the built-in three-service sample currently creates five entries, including two empty Sunday duplicates, both with and without a Services heading. The checks record that existing behaviour; always review extracted services and notices before printing.

## Test cases for any new version

- Paste emails with a `Services` heading and emails without one.
- Recognise AM/PM services, weekday meetings and varied date formats.
- Manually add/edit/reorder services and announcements.
- Keep the rota after formatting a new email.
- Export both the two-copy A4 PDF and the editable JSON draft.
- Check nothing overflows the printable A5 halves, especially on busy weeks.
