# Codex instructions — High Church Notice Builder

This is a self-contained browser app in `index.html`, no build step, dependencies, external libraries, backend or external AI API. The app is intended for a nontechnical user who publishes via GitHub Pages and edits via Codex.

## Non-negotiable behaviour

- Preserve the landscape A4 output with **two identical A5 notice sheets side by side**, the church header, two-column blocks, rota and footer.
- Preserve download-as-PDF and export/import of editable JSON drafts. Keep all weekly notice content in the user's browser, not in GitHub, telemetry, or online services.
- Preserve a working “format email” parser and full manual editing. Never claim arbitrary unstructured email parsing is error-free; always ask users to review before printing.
- Avoid introducing paid APIs, external libraries, build requirements or server-side components without explicit user approval.
- Default to UK spelling, UK date/time formats, and A4 print sizes.
- Do not hard-code real ministers' emails, personal rota names, private documents, or live weekly notices into source control.
- Maintain backwards compatibility of existing saved JSON drafts and browser data where possible. Explain migrations otherwise.

## Before making a change

- Inspect the relevant parsing, data model, output rendering and PDF export functions.
- Test at least one email with heading 'Services', one email without that heading and a busy week with several notices.
- Check actual exported PDF fits A4 landscape, copies match exactly, and download works from a normal browser.
- Test that saving and re-opening an editable draft still works.
- Explain to the user what changed and any print or data compatibility effects.
