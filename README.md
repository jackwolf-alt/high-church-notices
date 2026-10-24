# Stornoway High Church Notice Builder

A static, browser-only notice-sheet maker. Paste an email, review the extracted services and notices, and export two matching A5 notices on one landscape A4 PDF. All processing is done locally in the browser. No database, build system, paid hosting, or API key is needed.

## Publish it as a permanent web app with GitHub Pages

1. Create a free GitHub account if you do not already have one.
2. Create a **public** repository called `high-church-notices` (or another name). Leave it empty.
3. Unzip this package. In the GitHub repository, choose **Add file > Upload files**, select the three files from the unzipped folder (`index.html`, `README.md`, `AGENTS.md`) plus the `.nojekyll` file if visible, and **Commit changes**. `index.html` must be at the top level of the repository — not inside a subfolder.
4. Under **Settings > Pages**, set **Source** to **Deploy from a branch**, **Branch** to `main`, **Folder** to `/(root)`, and **Save**.
5. Once published, the address should be `https://YOUR-USERNAME.github.io/high-church-notices/` (using your actual GitHub username and repository name).
6. Bookmark it, or in Safari on a Mac choose **File > Add to Dock**.

**Important:** GitHub Pages sites are public, and on a free GitHub plan the repository will also be public. The package contains no real minister email or named rota entries; do not commit weekly email text, drafts, or private church records to GitHub. The live form and PDF export work in the browser. If you need a website with restricted access, choose a private hosting setup instead.

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

## Test cases for any new version

- Paste emails with a `Services` heading and emails without one.
- Recognise AM/PM services, weekday meetings and varied date formats.
- Manually add/edit/reorder services and announcements.
- Keep the rota after formatting a new email.
- Export both the two-copy A4 PDF and the editable JSON draft.
- Check nothing overflows the printable A5 halves, especially on busy weeks.
