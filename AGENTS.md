# Codex instructions — Churchpress

Churchpress is a self-contained browser app in `index.html`, no build step, runtime libraries or external AI API. Firebase email/password login and approved membership are required before using the editor. As requested by the user, printing and downloads automatically archive the editable sheet (including rota and layout settings) before output. The app is intended for a nontechnical user who publishes via GitHub Pages and edits via Codex.

## Non-negotiable behaviour

- Preserve the landscape A4 output with **two identical A5 notice sheets side by side**, the church header, two-column blocks, rota and footer.
- Preserve download-as-PDF and export/import of editable JSON drafts. Keep pasted source emails, uploaded logos and credentials out of the shared archive. Approved users' printable sheet settings, services, notices and rota are automatically archived before printing/downloading, or via Save sheet now. Keep browser autosave and JSON draft compatibility. Never put weekly content in GitHub or telemetry; never persist passwords or login tokens in drafts/localStorage.
- Preserve a working “format email” parser and full manual editing. Never claim arbitrary unstructured email parsing is error-free; always ask users to review before printing.
- Avoid introducing paid APIs, external libraries, build requirements or server-side components without explicit user approval.
- Keep church selection tied to the public CHURCHES directory. Each church needs its own Firebase project/database, approved user list and church-scoped browser draft storage. Never carry a draft, token or loaded archive across a church switch.
- Follow the user-supplied Churchpress brand kit: preserve the full original transparent wordmark, its proportions/colours and clear space, on white or very pale backgrounds. Use Manrope throughout, with navy #06265E, blue #087CFA, paper blue #EDF5FF, ink #182338 and slate #53627A. Keep the church identity prominent on sheets; preserve landscape A4 and two matching A5 copies. Test text contrast for controls. Default Large body is 11 pt at 110% overall size; warn about overflow rather than silently shrinking content.
- Default to UK spelling, UK date/time formats, and A4 print sizes.
- Do not hard-code real ministers' emails, personal rota names, private documents, or live weekly notices into source control.
- Maintain backwards compatibility of existing saved JSON drafts and browser data where possible. Explain migrations otherwise.

## Before making a change

- Inspect the relevant parsing, data model, output rendering and PDF export functions.
- Test at least one email with heading 'Services', one email without that heading and a busy week with several notices.
- Check actual exported PDF fits A4 landscape, copies match exactly, and download works from a normal browser.
- Test that saving and re-opening an editable draft still works.
- Explain to the user what changed and any print or data compatibility effects.
