"""Browser regression checks; see README.md for the optional test tools."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Error
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextmanager
def serving():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def settle(page):
    page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')


def set_size(page, part, value):
    page.locator(f'#{part}Size').fill(str(value))
    settle(page)
    assert page.locator(f'#{part}SizeValue').inner_text() == f'{value}%'


def draft(page, path):
    with page.expect_download() as download:
        page.locator('#saveDraft').click()
    download.value.save_as(path)
    return json.loads(path.read_text())


def export_pdf(page, path):
    page.evaluate('window.__pdfText = []')
    with page.expect_download() as download:
        page.locator('#pdfTop').click()
    download.value.save_as(path)
    reader = PdfReader(path)
    assert len(reader.pages) == 1
    box = reader.pages[0].mediabox
    assert abs(float(box.width) - 841.8898) < .01
    assert abs(float(box.height) - 595.2756) < .01
    assert path.stat().st_size > 10000
    # Compare the canvas before JPEG's lossy compression, including the entire header and footer.
    assert page.evaluate('''() => {
      const c=window.__pdfCanvas, g=c.getContext('2d'), half=c.width/2;
      const a=g.getImageData(0,0,half,c.height).data, b=g.getImageData(half,0,half,c.height).data;
      return a.every((value,i)=>value===b[i]);
    }''')
    return page.evaluate('window.__pdfText')


def main():
    with tempfile.TemporaryDirectory(prefix='notice-tests-') as tmp, serving() as url, sync_playwright() as p:
        tmp = Path(tmp)
        executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
        browser = p.chromium.launch(**({'executable_path': executable} if executable else {}), args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1600, 'height': 1100}, accept_downloads=True)
        errors, external = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: external.append(r.url) if not r.url.startswith((url, 'data:', 'blob:')) else None)
        page.on('dialog', lambda d: d.accept())
        page.add_init_script('''
          const originalText=CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText=function(text,...args){
            (window.__pdfText ||= []).push({text,font:this.font,scale:this.getTransform().a});
            return originalText.call(this,text,...args);
          };
          const originalURL=HTMLCanvasElement.prototype.toDataURL;
          HTMLCanvasElement.prototype.toDataURL=function(...args){window.__pdfCanvas=this;return originalURL.apply(this,args)};
        ''')
        assert page.goto(url).status == 200
        page.evaluate('document.fonts.ready')
        assert page.evaluate("document.fonts.check('400 12px Montserrat') && document.fonts.check('700 12px Montserrat')")
        assert page.locator('#overallSize').input_value() == '110'
        assert 'Montserrat' in page.locator('.half').first.evaluate('(e)=>getComputedStyle(e).fontFamily')
        page.locator('#demoBtn').click()
        sample = page.locator('#emailInput').input_value()
        for name, email, expected_notices in [
            ('without heading', sample, 2),
            ('Services heading', 'Services\n' + sample, 2),
            ('busy week', sample + '\n\nNotices\nCoffee morning\nSaturday 7th November at 10am. Everyone welcome.\n\nBook stall\nBooks available after worship.\n\nChoir\nPractice on Thursday at 7pm.', 6),
        ]:
            page.locator('#emailInput').fill(email)
            page.locator('#extractBtn').click()
            settle(page)
            # Existing parser defect: three sample services become five, with two empty duplicates.
            assert page.locator('#serviceEditors .entry').count() == 5
            assert page.locator('#noticeEditors .entry').count() == expected_notices
            assert page.locator('#paper').evaluate('(e)=>e.children.length===2 && e.children[0].outerHTML===e.children[1].outerHTML')
            export_pdf(page, tmp / 'email.pdf')
            print(f'PASS email case: {name} (known parser duplicates unchanged)')
        page.locator('#demoBtn').click()
        settle(page)
        original = draft(page, tmp / 'draft.json')
        base = export_pdf(page, tmp / 'base.pdf')
        # Check the PDF transform for every section and prove other sections stay unchanged.
        targets = {'header': 'STORNOWAY', 'services': 'Services',
                   'notices': 'Youth Group', 'rota': 'DATE', 'footer': 'www.stornowayhighchurch.org.uk'}
        def scale_for(records, text):
            return next(r['scale'] for r in records if r['text'].startswith(text))
        for part, text in targets.items():
            set_size(page, part, 130)
            records = export_pdf(page, tmp / f'{part}.pdf')
            assert abs(scale_for(records,text) / scale_for(base,text) - 1.3) < 1e-6, part
            for other, other_text in targets.items():
                if other != part:
                    assert abs(scale_for(records,other_text) - scale_for(base,other_text)) < 1e-6, (part,other)
            # Scaled cards must still occupy exactly their available column width.
            for card in page.locator('.half').first.locator('.notice-col > .print-card').all():
                assert card.evaluate('(e)=>Math.abs(e.getBoundingClientRect().width-e.parentElement.getBoundingClientRect().width)<1'), part
            set_size(page, part, 100)
        set_size(page, 'overall', 130)
        combined = export_pdf(page, tmp / 'overall.pdf')
        for text in targets.values():
            assert abs(scale_for(combined,text) / scale_for(base,text) - 130/110) < 1e-6
        set_size(page, 'services', 125)
        set_size(page, 'notices', 85)
        saved = draft(page, tmp / 'sized.json')
        assert saved['settings']['sizes']['overall'] == 130
        assert saved['settings']['sizes']['services'] == 125
        assert saved['settings']['sizes']['notices'] == 85
        page.reload()
        assert page.locator('#servicesSize').input_value() == '125'
        page.locator('#resetSizes').click()
        assert page.locator('#overallSize').input_value() == '110'
        assert page.locator('#servicesSize').input_value() == '100'
        page.locator('#openDraft').set_input_files(tmp / 'sized.json')
        page.wait_for_function("document.getElementById('servicesSize').value==='125'")
        assert draft(page, tmp / 'roundtrip.json')['settings'] == saved['settings']
        # Old drafts reset the size controls to defaults rather than inheriting an unrelated draft.
        original['settings'].pop('sizes')
        (tmp / 'legacy.json').write_text(json.dumps(original))
        page.locator('#openDraft').set_input_files(tmp / 'legacy.json')
        page.wait_for_function("document.getElementById('servicesSize').value==='100'")
        assert page.locator('#overallSize').input_value() == '110'
        # Malformed and out-of-range draft sizes are safely normalised.
        original['settings']['sizes'] = {'overall': 999, 'services': -10, 'notices': 'bad', 'rota': None}
        (tmp / 'invalid-sizes.json').write_text(json.dumps(original))
        page.locator('#openDraft').set_input_files(tmp / 'invalid-sizes.json')
        page.wait_for_function("document.getElementById('overallSize').value==='150'")
        assert page.locator('#servicesSize').input_value() == '70'
        assert page.locator('#noticesSize').input_value() == '100'
        assert page.locator('#rotaSize').input_value() == '100'
        page.locator('#resetSizes').click()
        print('PASS individual and overall scaling, reset, autosave, current/legacy draft round trips')
        # Large content must warn, and the PDF must still have one page and matching copies.
        page.locator('#noticeEditors textarea').first.fill('A busy week with many notices. ' * 250)
        set_size(page, 'overall', 150)
        set_size(page, 'notices', 150)
        page.wait_for_function("document.getElementById('previewStatus').textContent==='Too much text'")
        export_pdf(page, tmp / 'overflow.pdf')
        assert page.locator('#feedback').inner_text().startswith('PDF downloaded, but')
        settle(page)
        assert 'printable space' in page.locator('#layoutFeedback').inner_text()
        assert page.locator('#feedback').inner_text().startswith('PDF downloaded, but')
        # Restore the sample for browser printing and offline tests.
        page.locator('#demoBtn').click()
        page.locator('#resetSizes').click()
        settle(page)
        page.pdf(path=str(tmp / 'print.pdf'), prefer_css_page_size=True)
        reader = PdfReader(tmp / 'print.pdf')
        assert len(reader.pages) == 1
        assert abs(float(reader.pages[0].mediabox.width) - 841.89) < 1
        font_names = [str(f.get_object().get('/BaseFont', '')) + str(f.get_object().get('/FontDescriptor', {}).get('/FontFamily', '')) for f in reader.pages[0]['/Resources']['/Font'].values()]
        assert any('Montserrat' in name for name in font_names), font_names
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#overallSize').scroll_into_view_if_needed()
        assert page.locator('#overallSize').is_visible()
        assert page.locator('#overallSize').evaluate('(e)=>e.getBoundingClientRect().right<=window.innerWidth')
        assert not external, external
        # Open the standalone file without any network; font and export must still work.
        offline = browser.new_page(accept_downloads=True)
        offline.add_init_script('''const original=HTMLCanvasElement.prototype.toDataURL;
          HTMLCanvasElement.prototype.toDataURL=function(...args){window.__pdfCanvas=this;return original.apply(this,args)};''')
        offline.context.set_offline(True)
        try:
            offline.goto((ROOT / 'index.html').as_uri())
        except Error as exc:
            if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(exc):
                raise
            # Some managed browsers prohibit file URLs. Exercise the unchanged standalone HTML
            # offline in an empty document, without disabling the browser's policy.
            print('SKIP file URL navigation: managed browser policy; testing offline HTML document instead')
            offline.close()
            offline = browser.new_page(accept_downloads=True)
            offline.context.set_offline(True)
            offline.evaluate('''() => {const original=HTMLCanvasElement.prototype.toDataURL;
              HTMLCanvasElement.prototype.toDataURL=function(...args){window.__pdfCanvas=this;return original.apply(this,args)}}''')
            offline.set_content((ROOT / 'index.html').read_text())
        offline.evaluate('document.fonts.ready')
        assert offline.evaluate("document.fonts.check('400 12px Montserrat')")
        offline.locator('#demoBtn').click()
        export_pdf(offline, tmp / 'offline.pdf')
        assert not errors, errors
        print('PASS overflow warnings, single-page print/PDF, pixel-identical canvas copies, Montserrat print font, mobile controls and offline export')
        browser.close()


if __name__ == '__main__':
    main()
