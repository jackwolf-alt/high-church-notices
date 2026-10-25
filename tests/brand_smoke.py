"""Churchpress brand identity, legibility, assets and export naming (synthetic Firebase)."""
import json
import re
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_smoke import serving,activate_for
from firebase_mock import FirebaseMock


def luminance(colour):
    channels=[int(value)/255 for value in re.findall(r'\d+',colour)[:3]]
    channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
    return sum(c*w for c,w in zip(channels,[.2126,.7152,.0722]))


def check_contrast(locator):
    style=locator.evaluate('(e)=>{const s=getComputedStyle(e);return {color:s.color,background:s.backgroundColor,size:parseFloat(s.fontSize),weight:Number(s.fontWeight)}}')
    lo,hi=sorted([luminance(style['color']),luminance(style['background'])])
    ratio=(hi+.05)/(lo+.05)
    large=style['size']>=24 or (style['size']>=18.666 and style['weight']>=700)
    assert ratio >= (3 if large else 4.5),(ratio,style)


def main():
    with serving() as url,sync_playwright() as p,tempfile.TemporaryDirectory() as tmp:
        browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        page=browser.new_page(accept_downloads=True,viewport={'width':1440,'height':1050})
        FirebaseMock(page)
        page.add_init_script('''const original=CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText=function(text,...args){(window.__brandText ||= []).push({text,font:this.font,scale:this.getTransform().a});return original.call(this,text,...args)};''')
        page.goto(url);page.evaluate('document.fonts.ready')
        assert page.title()=='Churchpress — Ready for Sunday'
        assert page.locator('#signInTitle').inner_text()=='Ready for Sunday.'
        assert 'Manrope' in page.evaluate('getComputedStyle(document.body).fontFamily')
        palette=page.evaluate('Object.fromEntries(["--navy","--blue","--paper-blue","--ink","--grey"].map(p=>[p,getComputedStyle(document.documentElement).getPropertyValue(p).trim()]))')
        assert palette=={'--navy':'#06265E','--blue':'#087CFA','--paper-blue':'#EDF5FF','--ink':'#182338','--grey':'#53627A'},palette
        check_contrast(page.locator('#archiveLogin .button.primary'))
        assert page.locator('[data-app-logo] img').count()==2
        for image in page.locator('[data-app-logo] img').all():
            assert image.get_attribute('alt')=='Churchpress'
            assert image.evaluate('(e)=>e.complete && e.naturalWidth===2172 && e.naturalHeight===724')
            assert image.evaluate('(e)=>getComputedStyle(e).objectFit')=='contain'
            assert image.evaluate('(e)=>getComputedStyle(e).filter')=='none'
        sources=page.locator('[data-app-logo] img').evaluate_all('(es)=>es.map(e=>e.src)')
        assert sources[0]==sources[1] and sources[0].startswith('data:image/png;base64,')
        # Mock sign-in using the already installed fixture.
        page.locator('#archiveEmail').fill('sample@example.test');page.locator('#archivePassword').fill('synthetic-password');page.locator('#archiveLogin button[type=submit]').click()
        page.wait_for_selector('#application:visible');page.wait_for_function("!document.querySelector('#archiveLogin button[type=submit]').disabled")
        check_contrast(page.locator('#pdfTop'))
        check_contrast(page.locator('[data-workspace-tab=prepare]'))
        page.locator('#demoBtn').click()
        assert 'Montserrat' in page.locator('.paper').evaluate('(e)=>getComputedStyle(e).fontFamily')
        body_size=page.locator('.paper .print-card p').first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')
        assert abs(body_size*72/96-8.15)<.01
        with page.expect_download() as download:page.locator('#pdfTop').click()
        assert download.value.suggested_filename=='Churchpress-2026-11-01.pdf'
        records=page.evaluate('window.__brandText')
        assert any(r['text']=='CLEANING' for r in records) and any(r['text']=='WELCOME' for r in records), 'Restore original rota labels'
        body=next(r for r in records if r['text'].startswith('The youth group'))
        pixels=float(re.search(r'([\d.]+)px',body['font'])[1]);assert 'Montserrat' in body['font']
        assert abs(pixels/(240/72)-8.18)<.01,body
        page.wait_for_function("!document.getElementById('pdfTop').disabled")
        activate_for(page,'#saveDraft')
        with page.expect_download() as download:page.locator('#saveDraft').click()
        assert download.value.suggested_filename=='Churchpress-2026-11-01-draft.json'
        target=Path(tmp)/'draft.json';download.value.save_as(target)
        assert json.loads(target.read_text())['format']=='stornoway-high-church-notices','Retain the legacy draft format for compatibility'
        print('PASS Churchpress palette, full original transparent logo/proportions, Manrope UI and original Montserrat print body, action contrast and branded filenames with legacy draft compatibility')
        browser.close()


if __name__=='__main__':main()
