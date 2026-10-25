"""Firebase REST browser integration tests with synthetic, intercepted responses (no live account)."""
import json
import shutil
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_smoke import serving, settle


def main():
    with serving() as url, sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        page = browser.new_page(accept_downloads=True)
        requests, writes, errors, pending = [], [], [], []
        state = {'approved': True, 'deny': False, 'reset': False, 'older': False, 'hold': False}
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        week = {'name': 'projects/demo-church/databases/(default)/documents/noticeArchive/synthetic-week', 'fields': {
            'title': {'stringValue': '<img src=x onerror=alert(1)> Youth group'},
            'weekDate': {'stringValue': '2026-11-01'},
            'content': {'stringValue': json.dumps({'services': [{'heading': '11am Sunday 1st November', 'body': 'Sample service'}],
                'notices': [{'title': 'Youth Group', 'body': '<script>throw new Error("unsafe")</script> Bring a friend.', 'column': 'right'}]})}}}
        def respond(route):
            request = route.request
            requests.append(request)
            if request.method == 'OPTIONS':
                route.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*'}); return
            body = request.post_data_json if request.post_data else None
            status, result = 200, {}
            if 'signInWithPassword' in request.url:
                result = {'localId': 'approved-user', 'idToken': 'synthetic-id-token', 'refreshToken': 'synthetic-refresh-token', 'expiresIn': '1'}
            elif 'securetoken.googleapis.com' in request.url:
                result = {'id_token': 'synthetic-refreshed-id-token', 'refresh_token': 'synthetic-refreshed-refresh-token', 'expires_in': '3600'}
            elif 'sendOobCode' in request.url:
                state['reset'] = True
            elif '/members/' in request.url:
                result = {'fields': {'enabled': {'booleanValue': state['approved']}}}
            elif ':commit' in request.url:
                writes.append(body);result = {'writeResults': [{}]}
            elif '/noticeArchive' in request.url:
                if state['hold']:
                    pending.append(route)
                    return
                if state['deny']:
                    status, result = 403, {'error': {'message': 'Permission denied'}}
                else:
                    if 'pageToken=older-token' in request.url:
                        state['older'] = True
                        result = {'documents': []}
                    else:
                        result = {'documents': [week], 'nextPageToken': 'older-token'}
            else:
                raise AssertionError(request.url)
            route.fulfill(status=status, content_type='application/json', body=json.dumps(result), headers={'Access-Control-Allow-Origin': '*'})
        page.route('https://*.googleapis.com/**', respond)
        page.goto(url)
        page.locator('#demoBtn').click()
        settle(page)
        assert not requests, 'Local editing must never contact Firebase'
        page.locator('#firebaseProject').fill('demo-church')
        page.locator('#firebaseKey').fill('AIza' + 'x' * 30)
        page.locator('#connectArchive').click()
        def login():
            page.locator('#archiveEmail').fill('sample@example.test')
            page.locator('#archivePassword').fill('synthetic-password')
            page.locator('#archiveLogin button[type=submit]').click()
        login()
        page.wait_for_selector('#archiveAccount:visible')
        page.wait_for_selector('[data-archive-group="notices"]', state='attached')
        assert any('securetoken.googleapis.com' in request.url for request in requests), 'Expired login tokens must refresh'
        assert page.locator('#archivePassword').input_value() == ''
        assert 'Youth group' in page.locator('#archiveResults').inner_text()
        assert page.locator('#archiveResults img, #archiveResults script').count() == 0
        before = page.locator('#noticeEditors .entry').count()
        page.locator('#archiveResults details').first.locator('summary').click()
        page.locator('[data-archive-group="notices"]').click()
        assert page.locator('#noticeEditors .entry').count() == before + 1
        page.locator('#archiveSearch').fill('unmatched search')
        assert page.locator('[data-archive-group]').count() == 0
        page.locator('#archiveSearch').fill('youth')
        assert page.locator('[data-archive-group="notices"]').count() == 1
        page.locator('#archiveOlder').click()
        page.wait_for_function("document.getElementById('archiveOlder').hidden")
        assert state['older']
        page.locator('#archiveTitle').fill('Synthetic archived week')
        page.locator('#archivePublish').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.startsWith('Published')")
        assert len(writes) == 1
        write = writes[0]['writes'][0]
        fields = write['update']['fields']
        assert set(fields) == {'title', 'weekDate', 'content', 'createdBy'}
        assert set(json.loads(fields['content']['stringValue'])) == {'services', 'notices'}
        assert write['currentDocument'] == {'exists': False}
        assert write['updateTransforms'] == [{'fieldPath': 'createdAt', 'setToServerValue': 'REQUEST_TIME'}]
        with page.expect_download() as download:
            page.locator('#saveDraft').click()
        path = Path(tmp) / 'draft.json'; download.value.save_as(path)
        stored = page.evaluate('JSON.stringify({...localStorage})') + path.read_text()
        assert all(secret not in stored for secret in ['synthetic-password', 'synthetic-id-token', 'synthetic-refresh-token', 'synthetic-refreshed-id-token', 'synthetic-refreshed-refresh-token', 'sample@example.test'])
        # A late archive response must never repopulate private results after sign-out.
        state['hold'] = True
        page.locator('#archiveRefresh').click()
        for _ in range(50):
            if pending:
                break
            page.wait_for_timeout(20)
        assert pending
        page.locator('#archiveSignOut').click()
        pending.pop().fulfill(status=200,content_type='application/json',body=json.dumps({'documents':[week]}),headers={'Access-Control-Allow-Origin':'*'})
        page.wait_for_function("!document.querySelector('#archiveLogin button[type=submit]').disabled")
        assert page.locator('#archiveResults').inner_text() == ''
        assert page.locator('#archiveStatus').inner_text().startswith('Signed out')
        state['hold'] = False
        login()
        page.wait_for_selector('#archiveAccount:visible')
        page.wait_for_selector('[data-archive-group="notices"]',state='attached')
        state['deny'] = True
        page.locator('#archiveRefresh').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.startsWith('Archive access denied')")
        page.locator('#archiveSignOut').click()
        assert page.locator('#archiveResults').inner_text() == ''
        assert page.locator('#archiveAccount').is_hidden()
        assert page.locator('#noticeEditors .entry').count() == before + 1
        state['deny'] = False;state['approved'] = False
        login()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.includes('not been approved')")
        assert page.locator('#archiveAccount').is_hidden()
        page.locator('#archiveResetPassword').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.includes('password reset email')")
        assert state['reset']
        page.reload()
        assert page.locator('#firebaseProject').input_value() == 'demo-church'
        assert page.locator('#archiveAccount').is_hidden(), 'Do not persist tokens across reloads'
        assert not errors, errors
        print('PASS Firebase REST UI: login, membership, search/pagination, escaped content, reuse, explicit publish/privacy, reset, denied access, sign-out and local draft isolation (mocked service)')
        browser.close()


if __name__ == '__main__':
    main()
