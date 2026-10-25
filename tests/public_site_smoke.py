"""Public marketing site, isolated Hosting output and synthetic provisioning checks."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
from urllib.parse import urlparse, unquote
from unittest.mock import patch

from playwright.sync_api import sync_playwright
from browser_smoke import ROOT, serving
from brand_smoke import check_contrast


def check_staging():
    dashboard = json.loads((ROOT / 'firebase.json').read_text())['hosting']
    public = json.loads((ROOT / 'firebase.public.json').read_text())['hosting']
    assert dashboard['public'] == 'dist' and 'site' not in dashboard
    assert public['public'] == 'dist-public'
    assert public['site'] == 'churchpress-public-833739660900'
    workflow = (ROOT / '.github/workflows/firebase-hosting.yml').read_text()
    assert "vars.FIREBASE_PUBLIC_SITE_ENABLED == 'true'" in workflow
    assert '--config firebase.public.json' in workflow
    assert 'public/**' in workflow
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        shutil.copytree(ROOT / 'public', folder / 'public')
        (folder / 'scripts').mkdir()
        for name in ('prepare-hosting.sh', 'prepare-public-hosting.sh'):
            shutil.copyfile(ROOT / 'scripts' / name, folder / 'scripts' / name)
        # Ensure accidental repository files cannot enter the public upload.
        (folder / 'index.html').write_text('synthetic private dashboard')
        (folder / 'gha-creds-test.json').write_text('synthetic credential marker')
        (folder / 'public' / 'unexpected-secret.txt').write_text('synthetic marker')
        subprocess.run(['bash', 'scripts/prepare-hosting.sh'], cwd=folder, check=True)
        subprocess.run(['bash', 'scripts/prepare-public-hosting.sh'], cwd=folder, check=True)
        public_files = [f for f in (folder / 'dist-public').rglob('*') if f.is_file()]
        assert len(public_files) == 10
        assert (folder / 'dist' / 'index.html').read_text() == 'synthetic private dashboard'
        for file in public_files:
            original = folder / 'public' / file.relative_to(folder / 'dist-public')
            assert file.read_bytes() == original.read_bytes()
            assert b'synthetic marker' not in file.read_bytes()
        rerun = subprocess.run(['bash', 'scripts/prepare-public-hosting.sh'], cwd=folder, capture_output=True)
        assert rerun.returncode != 0
    print('PASS separate public/dashboard Hosting sites and allowlisted staging')


def check_provisioning():
    source = (ROOT / 'scripts/setup-public-hosting.sh').read_text().split("<<'PYTHON'\n", 1)[1].split('\nPYTHON', 1)[0]
    for exists in (True, False):
        calls = []

        def respond(request, timeout):
            calls.append(request)
            assert request.headers['Authorization'] == 'Bearer synthetic-token'
            assert 'high-church-notices/sites' in request.full_url
            if request.data is None and not exists:
                raise urllib.error.HTTPError(request.full_url, 404, 'Not found', {}, None)
            if request.data is not None:
                assert request.full_url.endswith('?siteId=churchpress-public-833739660900')
            return io.BytesIO(json.dumps({'name': 'projects/high-church-notices/sites/churchpress-public-833739660900'}).encode())

        with patch('subprocess.check_output', return_value='synthetic-token\n'), patch('urllib.request.urlopen', side_effect=respond), redirect_stdout(io.StringIO()):
            exec(compile(source, 'setup-public-hosting', 'exec'), {'__name__': '__main__'})
        assert len(calls) == (1 if exists else 2)
    # A permission failure must not trigger site creation or claim success.
    error = urllib.error.HTTPError('https://example.test', 403, 'Forbidden', {}, None)
    with patch('subprocess.check_output', return_value='synthetic-token\n'), patch('urllib.request.urlopen', side_effect=error) as request:
        try:
            exec(compile(source, 'setup-public-hosting', 'exec'), {'__name__': '__main__'})
            raise AssertionError('Permission failure ignored')
        except SystemExit as failure:
            assert 'HTTP 403' in str(failure)
        assert request.call_count == 1
    print('PASS new/existing public site and permission errors (mocked Google; no live changes)')


def main():
    check_staging()
    check_provisioning()
    with serving() as url, sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'), args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors, failed, requests = [], [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: failed.append(response.url) if response.status >= 400 else None)
        page.on('request', lambda request: requests.append(request.url))
        page.goto(url + '/public/')
        page.evaluate('document.fonts.ready')
        assert page.title() == 'Churchpress — Your church notices, ready for Sunday'
        assert page.locator('h1').count() == 1
        assert page.locator('link[rel=canonical]').get_attribute('href') == 'https://churchpress.co.uk/'
        assert 'Manrope' in page.locator('body').evaluate('(e)=>getComputedStyle(e).fontFamily')
        assert page.locator('.price').inner_text() == '£11.99 / month'
        assert page.locator('.trial-label').inner_text() == '30-day free trial'
        for link in page.locator('a[href^="mailto:"]').all():
            assert unquote(urlparse(link.get_attribute('href')).path) == 'jackwolf@jackwolfproductions.com'
        trial = page.get_by_role('link', name='Arrange your free trial').first.get_attribute('href')
        assert '30-day free trial' in unquote(trial)
        dashboard_links = page.locator('a[href="https://dashboard.churchpress.co.uk"]')
        assert dashboard_links.count() >= 3
        for link in page.locator('a[href^="#"]').all():
            assert page.locator(link.get_attribute('href')).count() == 1
        page.locator('img').evaluate_all('(images)=>images.forEach(image=>image.loading="eager")')
        page.wait_for_function('Array.from(document.images).every(image=>image.complete && image.naturalWidth>0)')
        for image in page.locator('img').all():
            assert image.get_attribute('alt')
            assert image.evaluate('(e)=>e.complete && e.naturalWidth>0')
        logo = page.locator('.site-header .brand img')
        assert logo.evaluate('(e)=>e.naturalWidth===2172 && e.naturalHeight===724')
        assert 'fictional' in page.locator('figcaption').inner_text()
        for selector in ('.button-primary', '.button-light', '.button-outline', '.trial-label'):
            check_contrast(page.locator(selector).first)
        search = page.locator('#example-search')
        search.fill('  COFFEE  ')
        assert page.locator('.example-notice:visible').count() == 1
        assert page.locator('#example-count').inner_text() == '1 example notice'
        summary = page.locator('.example-notice:visible summary')
        summary.focus();page.keyboard.press('Enter')
        assert page.locator('.example-notice:visible').evaluate('(e)=>e.open')
        assert 'Saturday' in page.locator('.example-notice:visible').inner_text()
        search.fill('no matching notice')
        assert page.locator('#example-empty').is_visible()
        assert page.locator('.example-notice:visible').count() == 0
        search.fill('')
        assert page.locator('.example-notice:visible').count() == 3
        assert page.evaluate('localStorage.length===0 && sessionStorage.length===0')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 950})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            assert page.locator('.site-header a[href="https://dashboard.churchpress.co.uk"]').is_visible()
            assert page.locator('.price').is_visible()
        page.locator('.faqs summary').first.focus();page.keyboard.press('Enter')
        assert page.locator('.faqs details').first.evaluate('(e)=>e.open')
        page.goto(url + '/public/privacy.html')
        assert page.locator('h1').inner_text() == 'Website privacy'
        assert 'jackwolf@jackwolfproductions.com' in page.locator('main').inner_text()
        assert not errors, errors
        assert not failed, failed
        assert all(request.startswith((url, 'data:')) for request in requests), requests
        print('PASS public pricing/CTA links, keyboard demo/FAQ, fonts/brand, responsive layout, privacy and no external requests/storage')
        browser.close()


if __name__ == '__main__':
    main()
