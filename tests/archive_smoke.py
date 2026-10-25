"""Sign-in gate, automatic archive and specific-notice recall against synthetic Firebase REST."""
import json
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_smoke import serving, settle, export_pdf
from firebase_mock import FirebaseMock
from pypdf import PdfReader


def wait_idle(page):
    page.wait_for_function("!document.querySelector('.editor').inert && !document.getElementById('pdfTop').disabled")


def main():
    with serving() as url, sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        page = browser.new_page(accept_downloads=True)
        errors, downloads = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('download', lambda d: downloads.append(d))
        page.on('dialog', lambda d: d.accept())
        old_week = {'name': 'projects/demo-church/databases/(default)/documents/noticeArchive/synthetic-week', 'fields': {
            'title': {'stringValue': '<img src=x onerror=alert(1)> Youth group'}, 'weekDate': {'stringValue': '2026-11-01'},
            'content': {'stringValue': json.dumps({'services': [{'heading': '11am Sunday 1st November', 'body': 'Sample service'}],
                'notices': [{'title': 'Youth Group', 'body': '<script>throw new Error("unsafe")</script> Bring a friend.', 'column': 'right'}]})}}}
        firebase = FirebaseMock(page, [old_week])
        page.add_init_script('''
          const originalText=CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText=function(text,...args){(window.__pdfText ||= []).push({text,font:this.font,scale:this.getTransform().a});return originalText.call(this,text,...args)};
          const originalURL=HTMLCanvasElement.prototype.toDataURL;
          HTMLCanvasElement.prototype.toDataURL=function(...args){window.__pdfCanvas=this;return originalURL.apply(this,args)};
          window.__prints=0;window.print=()=>{window.dispatchEvent(new Event('beforeprint'));if(!document.body.classList.contains('print-blocked'))window.__prints++;window.dispatchEvent(new Event('afterprint'))};
        ''')
        page.goto(url)
        assert page.locator('#application').is_hidden()
        assert page.locator('#signInScreen').is_visible()
        assert not firebase.calls, 'Opening the login screen must not contact Firebase'
        page.evaluate("document.getElementById('pdfTop').click()")
        assert not firebase.calls and not downloads
        assert page.locator('#firebaseProject').input_value() == 'high-church-notices'
        page.locator('#archiveConnection > summary').click()
        page.locator('#firebaseProject').fill('demo-church')
        page.locator('#firebaseKey').fill('AIza' + 'x' * 30)
        page.locator('#connectArchive').click()
        firebase.approved = False
        page.locator('#archiveEmail').fill('sample@example.test')
        page.locator('#archivePassword').fill('synthetic-password')
        page.locator('#archiveLogin button[type=submit]').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.includes('not been approved')")
        assert page.locator('#application').is_hidden()
        firebase.approved = True
        firebase.login()
        assert firebase.refreshed
        assert page.locator('#signInScreen').is_hidden()
        page.locator('#demoBtn').click()
        page.locator('#rotaEditors [data-field="cleaning"]').first.fill('Synthetic team')
        page.locator('#servicesSize').fill('125')
        page.locator('#archiveTitle').fill('Synthetic archived week')
        before = page.locator('#noticeEditors .entry').count()
        # Recall a single notice from the legacy archive without replacing the sheet or rota.
        page.locator('#archiveSearch').fill('Youth group')
        page.locator('#archiveResults details').first.locator('summary').click()
        assert page.locator('#archiveResults img, #archiveResults script').count() == 0
        page.locator('[data-archive-group="notices"]').click()
        assert page.locator('#noticeEditors .entry').count() == before + 1
        assert page.locator('#rotaEditors [data-field="cleaning"]').first.input_value() == 'Synthetic team'
        page.locator('#archiveSearch').fill('unmatched search')
        assert page.locator('[data-archive-group]').count() == 0
        page.locator('#archiveSearch').fill('')
        page.locator('#archiveOlder').click()
        page.wait_for_function("document.getElementById('archiveOlder').hidden")
        assert firebase.older
        # Ctrl+P must not print an unsaved version or silently archive it.
        page.evaluate('window.print()')
        assert page.evaluate('window.__prints') == 0
        assert not firebase.commits
        export_pdf(page,tmp / 'sheet.pdf')
        wait_idle(page)
        assert len(firebase.commits) == 1
        fields = firebase.commits[0]['writes'][0]['update']['fields']
        saved = json.loads(fields['content']['stringValue'])
        assert set(saved) == {'services', 'notices', 'sheet'}
        assert saved['sheet']['rota'][0]['cleaning'] == 'Synthetic team'
        assert saved['sheet']['sizes']['services'] == 125
        assert 'emailInput' not in saved['sheet'] and 'logo' not in saved['sheet']
        assert set(fields) == {'title','weekDate','content','createdBy'}
        # PDF, print and draft download of the same content must share a single immutable snapshot.
        export_pdf(page,tmp / 'same.pdf');wait_idle(page)
        page.locator('#printTop').click();wait_idle(page)
        assert page.evaluate('window.__prints') == 1
        with page.expect_download() as download:
            page.locator('#saveDraft').click()
        path = tmp / 'draft.json'; download.value.save_as(path);wait_idle(page)
        assert len(firebase.commits) == 1
        page.locator('#archivePublish').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.includes('Unchanged sheets are not duplicated')")
        assert len(firebase.commits) == 1
        stored = page.evaluate('JSON.stringify({...localStorage})') + path.read_text()
        assert all(secret not in stored for secret in ['synthetic-password','synthetic-id-token','synthetic-refresh-token','synthetic-refreshed-id-token','synthetic-refreshed-refresh-token','sample@example.test'])
        # A revision gets a new snapshot. Reopening the saved version restores the rota and sizes.
        page.locator('#rotaEditors [data-field="cleaning"]').first.fill('Revised synthetic team')
        export_pdf(page,tmp / 'revised.pdf');wait_idle(page)
        assert len(firebase.commits) == 2
        page.locator('#archiveRefresh').click()
        page.wait_for_function("!document.getElementById('archiveRefresh').disabled")
        sheet_id = next(iter(firebase.documents))
        page.locator(f'[data-open-sheet="{sheet_id}"]').evaluate('(e)=>e.closest("details").open=true')
        page.locator(f'[data-open-sheet="{sheet_id}"]').click()
        assert page.locator('#rotaEditors [data-field="cleaning"]').first.input_value() == 'Synthetic team'
        assert page.locator('#servicesSize').input_value() == '125'
        assert page.locator('#emailInput').input_value() == ''
        # Across reloads, deterministic IDs still prevent duplicate saves.
        page.reload();assert page.locator('#application').is_hidden();firebase.login()
        page.locator('#archiveTitle').fill('Synthetic archived week')
        export_pdf(page,tmp / 'after-reload.pdf');wait_idle(page)
        assert len(firebase.commits) == 2
        # An existing deterministic ID must match its content and author before reuse.
        document=next(iter(firebase.documents.values()))
        saved_title=document['fields']['title']['stringValue']
        document['fields']['title']['stringValue']='Conflicting synthetic title'
        count=len(downloads)
        page.locator('#pdfTop').click()
        page.wait_for_function("document.getElementById('feedback').textContent.includes('conflicts with this sheet')")
        wait_idle(page)
        assert len(downloads)==count
        document['fields']['title']['stringValue']=saved_title
        # Denied save must stop PDF, print and draft output while preserving local edits.
        firebase.deny = True
        n = len(downloads)
        page.locator('#noticeEditors textarea').first.fill('Unsaved synthetic revision')
        for button in ['pdfTop','printTop','saveDraft']:
            page.locator('#'+button).click()
            page.wait_for_function("document.getElementById('feedback').textContent.includes('No output was produced')")
            wait_idle(page)
        assert len(downloads) == n and page.evaluate('window.__prints') == 0
        assert page.locator('#noticeEditors textarea').first.input_value() == 'Unsaved synthetic revision'
        # Native printing also blocks the newly modified, unsaved sheet.
        page.pdf(path=str(tmp / 'blocked-print.pdf'),prefer_css_page_size=True)
        text=''.join(p.extract_text() for p in PdfReader(tmp / 'blocked-print.pdf').pages)
        assert 'Print button' in text and 'Unsaved synthetic revision' not in text
        firebase.deny = False
        # Signing out during an archive save must prevent output and keep the login screen in place.
        firebase.hold_commit = True
        page.locator('#pdfTop').click()
        for _ in range(100):
            if firebase.pending:break
            page.wait_for_timeout(20)
        assert firebase.pending
        page.locator('#archiveSignOut').click()
        route, body=firebase.pending.pop();firebase.commit(route,body)
        page.wait_for_function("!document.getElementById('pdfTop').disabled")
        assert page.locator('#application').is_hidden() and len(downloads) == n
        assert page.locator('#archiveResults').inner_text() == ''
        firebase.hold_commit = False
        page.locator('#archiveResetPassword').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.includes('password reset email')")
        assert firebase.reset
        assert not errors, errors
        print('PASS login gate, approval, token refresh, specific-notice recall, full-sheet restore, automatic print/PDF/JSON saves, deduplication across reloads, privacy, failed-save/native-print blocking, sign-out during save and password reset (mocked Firebase)')
        browser.close()


if __name__ == '__main__':
    main()
