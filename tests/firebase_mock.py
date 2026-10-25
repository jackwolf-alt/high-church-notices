"""Synthetic Firebase REST fixture. It never uses the real project's credentials or data."""
import json


class FirebaseMock:
    def __init__(self, page, weeks=None):
        self.page = page
        self.calls = []
        self.documents = {}
        self.weeks = weeks or []
        self.approved = True
        self.deny = False
        self.hold_list = False
        self.hold_commit = False
        self.pending = []
        self.commits = []
        self.refreshed = False
        self.reset = False
        self.older = False
        page.route('https://*.googleapis.com/**', self.respond)

    @staticmethod
    def reply(route, result=None, status=200):
        route.fulfill(status=status, content_type='application/json', body=json.dumps(result or {}), headers={'Access-Control-Allow-Origin': '*'})

    def commit(self, route, body):
        write = body['writes'][0]
        doc = write['update']
        self.commits.append(body)
        self.documents[doc['name'].split('/')[-1]] = {**doc, 'fields': {**doc['fields'], 'createdAt': {'timestampValue': '2026-11-01T12:00:00Z'}}}
        self.reply(route, {'writeResults': [{}]})

    def respond(self, route):
        request = route.request
        self.calls.append(request)
        if request.method == 'OPTIONS':
            route.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*'})
            return
        url = request.url
        body = request.post_data_json if request.post_data and 'securetoken' not in url else None
        if 'signInWithPassword' in url:
            self.reply(route, {'localId': 'approved-user', 'idToken': 'synthetic-id-token', 'refreshToken': 'synthetic-refresh-token', 'expiresIn': '1'})
        elif 'securetoken.googleapis.com' in url:
            self.refreshed = True
            self.reply(route, {'id_token': 'synthetic-refreshed-id-token', 'refresh_token': 'synthetic-refreshed-refresh-token', 'expires_in': '3600'})
        elif 'sendOobCode' in url:
            self.reset = True
            self.reply(route)
        elif self.deny:
            self.reply(route, {'error': {'message': 'Permission denied'}}, 403)
        elif '/members/' in url:
            self.reply(route, {'fields': {'enabled': {'booleanValue': self.approved}}})
        elif ':commit' in url:
            if self.hold_commit:
                self.pending.append((route, body))
            else:
                self.commit(route, body)
        elif '/noticeArchive/' in url:
            doc = self.documents.get(url.split('/')[-1])
            self.reply(route, doc or {'error': {'message': 'Not found'}}, 200 if doc else 404)
        elif '/noticeArchive' in url:
            if self.hold_list:
                self.pending.append((route, None))
            elif 'pageToken=older-token' in url:
                self.older = True
                self.reply(route, {'documents': []})
            else:
                self.reply(route, {'documents': [*self.documents.values(), *self.weeks], **({'nextPageToken': 'older-token'} if self.weeks else {})})
        else:
            raise AssertionError(url)

    def login(self):
        self.page.locator('#archiveEmail').fill('sample@example.test')
        self.page.locator('#archivePassword').fill('synthetic-password')
        self.page.locator('#archiveLogin button[type=submit]').click()
        self.page.wait_for_selector('#application:visible')
        self.page.wait_for_function("!document.querySelector('#archiveLogin button[type=submit]').disabled")
