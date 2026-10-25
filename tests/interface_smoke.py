"""Screen layout, church selection and local/cloud context separation (mocked Firebase only)."""
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_smoke import serving, activate_for
from firebase_mock import FirebaseMock

ROOT=Path(__file__).resolve().parents[1]


def main():
    with serving() as url,sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        firebase=FirebaseMock(page)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('dialog',lambda d:d.accept())
        html=(ROOT/'index.html').read_text()
        # An additional church exists only in this test. Never provision or query a real second project.
        marker="const CHURCHES=["
        second="{id:'riverside-test',name:'Riverside Test Church',projectId:'demo-riverside',apiKey:'AIza"+'x'*30+"',logo:''},"
        html=html.replace(marker,marker+'\n '+second)
        # Keep Stornoway selected initially despite adding the synthetic test record first.
        page.route(url+'/',lambda route:route.fulfill(content_type='text/html',body=html))
        legacy={'churchName':'Stornoway High Church','typeSize':'normal',
                'services':[{'id':1,'heading':'Synthetic legacy service','body':'Local private first-church draft'}],
                'notices':[{'id':2,'title':'Synthetic legacy notice','body':'Private old notice','column':'right'}],
                'rota':[{'week':'Sunday','cleaning':'Synthetic first-church rota','welcome':'','tea':''},{'week':'','cleaning':'','welcome':'','tea':''}]}
        page.add_init_script("if(location.origin==="+json.dumps(url)+"&&!localStorage.getItem('seeded')){localStorage.setItem('seeded','true');localStorage.setItem('high-church-selected-church-v1','stornoway-high-church');localStorage.setItem('stornoway-high-church-notices-v3',"+json.dumps(json.dumps(legacy))+");}")
        page.goto(url)
        assert page.locator('#churchSelect option').count()==2
        assert page.locator('#churchSelect').input_value()=='stornoway-high-church'
        assert page.locator('#application').is_hidden()
        assert page.locator('#connectArchive,#firebaseProject,#firebaseKey').count()==0
        assert not firebase.calls
        firebase.login()
        assert page.locator('#typeSize').input_value()=='normal', 'Legacy V3 text preset must not change during migration'
        assert page.locator('#serviceEditors textarea').first.input_value()=='Local private first-church draft'
        assert page.locator('#rotaEditors [data-field=cleaning]').first.input_value()=='Synthetic first-church rota'
        assert page.locator('[data-workspace-panel]:visible').count()==1
        assert 'Manrope' in page.evaluate('getComputedStyle(document.body).fontFamily')
        assert 'Montserrat' in page.locator('.paper').evaluate('(e)=>getComputedStyle(e).fontFamily')
        activate_for(page,'#noticesSize')
        assert page.locator('[data-workspace-tab=print]').get_attribute('aria-selected')=='true'
        # Accessible tab keyboard handling and no document-wide mobile horizontal overflow.
        page.locator('[data-workspace-tab=print]').focus();page.keyboard.press('ArrowRight')
        assert page.locator('[data-workspace-tab=archive]').get_attribute('aria-selected')=='true'
        page.keyboard.press('Home')
        assert page.locator('[data-workspace-tab=prepare]').get_attribute('aria-selected')=='true'
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_function('document.querySelector("#paper").getBoundingClientRect().width<=document.querySelector(".preview-scroll").clientWidth')
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Mobile page must not overflow horizontally'
        assert page.locator('[data-app-logo]').count()==2
        # Local logo uploads belong to the church sheet; the product keeps its Churchpress wordmark.
        page.locator('#logoUpload').set_input_files({'name':'synthetic.svg','mimeType':'image/svg+xml','buffer':b'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="60"><rect fill="white" width="240" height="60"/></svg>'})
        page.wait_for_selector('.topbar [data-app-logo] img')
        page.locator('#archiveSignOut').click()
        assert page.locator('#application').is_hidden()
        page.locator('#churchSelect').select_option('riverside-test')
        assert 'Riverside' in page.locator('#archiveStatus').inner_text()
        assert page.locator('#serviceEditors .entry').count()==0
        assert page.locator('#noticeEditors .entry').count()==0
        assert page.locator('#rotaEditors [data-field=cleaning]').first.input_value()==''
        assert page.locator('#website').input_value()==''
        assert page.locator('.paper .custom-logo').count()==0, 'Previous church logo must not leak into another church'
        assert page.locator('[data-app-logo] img').count()==2, 'Churchpress wordmark remains the product identity'
        firebase.approved=False
        page.locator('#archiveEmail').fill('sample@example.test');page.locator('#archivePassword').fill('synthetic-password');page.locator('#archiveLogin button[type=submit]').click()
        page.wait_for_function("document.getElementById('archiveStatus').textContent.includes('not been approved')")
        assert page.locator('#application').is_hidden(), 'Approval in the first church does not authorise the second church'
        assert any('/projects/demo-riverside/' in request.url for request in firebase.calls)
        firebase.approved=True;firebase.login()
        page.locator('#demoBtn').click();activate_for(page,'#noticeEditors textarea')
        page.locator('#noticeEditors textarea').first.fill('Synthetic second-church draft')
        page.locator('#archiveSignOut').click();page.locator('#churchSelect').select_option('stornoway-high-church')
        firebase.login()
        assert page.locator('#serviceEditors textarea').first.input_value()=='Local private first-church draft'
        assert page.locator('#noticeEditors textarea').first.input_value()=='Private old notice'
        assert page.locator('#rotaEditors [data-field=cleaning]').first.input_value()=='Synthetic first-church rota'
        page.locator('#archiveSignOut').click();page.locator('#churchSelect').select_option('riverside-test')
        firebase.login()
        assert page.locator('#noticeEditors textarea').first.input_value()=='Synthetic second-church draft'
        page.reload()
        assert page.locator('#churchSelect').input_value()=='riverside-test'
        assert page.locator('#application').is_hidden()
        assert not errors,errors
        print('PASS church dropdown, legacy draft migration, separate drafts/logos per church, approval per project, selected-project REST routing, remembered selection, tabs/keyboard, fonts and responsive fit')
        browser.close()


if __name__=='__main__':
    main()
