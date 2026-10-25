# Codex instructions — Churchpress

Churchpress is a self-contained browser app in `index.html`, no build step, runtime libraries or external AI API. Firebase email/password login and approved membership are required before using the editor. As requested by the user, printing and downloads automatically archive the editable sheet (including rota and layout settings) before output. The app is intended for a nontechnical user who publishes via Firebase Hosting (or GitHub Pages) and edits via Codex. Hosting deployment and browser-only Google Cloud Shell setup are documented in `firebase/HOSTING.md`. The GitHub workflow deploys only Hosting; preserve archive data and rules.

The public marketing site lives in `public/`, with its own `firebase.public.json` configuration, `dist-public/` upload and explicitly named Hosting site. Keep it separate from the root dashboard HTML and default Hosting site. Its browser-only deployment instructions are in `firebase/PUBLIC-SITE.md`. The shared workflow deploys it only when `FIREBASE_PUBLIC_SITE_ENABLED` is `true`. Public pricing is £11.99 per month with a 30-day free trial, arranged by email; do not imply automated billing or onboarding exists.

## Non-negotiable behaviour

- Preserve the landscape A4 output with **two identical A5 notice sheets side by side**, the church header, two-column blocks, rota and footer.
- Preserve download-as-PDF and export/import of editable JSON drafts. Keep pasted source emails, uploaded logos and credentials out of the shared archive. Approved users' printable sheet settings, services, notices and rota are automatically archived before printing/downloading, or via Save sheet now. Keep browser autosave and JSON draft compatibility. Never put weekly content in GitHub or telemetry; never persist passwords or login tokens in drafts/localStorage.
- Preserve a working “format email” parser and full manual editing. Never claim arbitrary unstructured email parsing is error-free; always ask users to review before printing.
- Avoid introducing paid APIs, external libraries, build requirements or server-side components without explicit user approval.
- Keep church selection tied to the public CHURCHES directory. Each church needs its own Firebase project/database, approved user list and church-scoped browser draft storage. Never carry a draft, token or loaded archive across a church switch.
- Apply the Churchpress brand kit to the interface only: full original wordmark, Manrope, navy #06265E, blue #087CFA, paper blue #EDF5FF, ink #182338 and slate #53627A. Test interface control contrast.
- The user explicitly requires the notice sheets to keep their pre-rebrand Montserrat typography, original size presets, monochrome styling, rota labels and two-A5-on-A4 layout. Do not apply product branding or interface font/size changes to the sheet or PDF. Preserve saved overall/section sizes, including the 110% overall default.
- Default to UK spelling, UK date/time formats, and A4 print sizes.
- Do not hard-code real ministers' emails, personal rota names, private documents, or live weekly notices into source control.
- Maintain backwards compatibility of existing saved JSON drafts and browser data where possible. Explain migrations otherwise.

## Before making a change

- Inspect the relevant parsing, data model, output rendering and PDF export functions.
- Test at least one email with heading 'Services', one email without that heading and a busy week with several notices.
- Check actual exported PDF fits A4 landscape, copies match exactly, and download works from a normal browser.
- Test that saving and re-opening an editable draft still works.
- Explain to the user what changed and any print or data compatibility effects.
