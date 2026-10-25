# Publish the Churchpress public website

The public website lives in `public/`. It advertises **£11.99 per month with a 30-day free trial**, links sign-in to **https://dashboard.churchpress.co.uk**, and sends enquiries/trial requests to **jackwolf@jackwolfproductions.com** using the visitor's email app. Trials are arranged manually: there is no checkout, payment collection, automatic trial provisioning or billing system.

The public site and dashboard are deliberately separate Firebase Hosting sites. Publishing the public website must never replace the dashboard's HTML or move its custom domain.

| Address | Firebase Hosting site | Uploaded content |
| --- | --- | --- |
| `dashboard.churchpress.co.uk` | existing default `high-church-notices` site | root `index.html` staged to `dist/` |
| `churchpress.co.uk` (and optionally `www`) | `churchpress-public-833739660900` | `public/` staged to `dist-public/` |

The public site uses `firebase.public.json`, which explicitly names the new site. The dashboard retains its existing configuration. The same GitHub workflow and Hosting-only deploy account can deploy both. No Firebase database, authentication or print settings change.

## One-time browser-only setup

1. Merge the public-site pull request. The dashboard will deploy as usual; the public deployment is skipped until enabled below.
2. Open [Google Cloud Shell](https://shell.cloud.google.com/?project=high-church-notices). In your existing repository folder run:

   ```sh
   cd ~/high-church-notices
   git switch main
   git pull --ff-only
   bash scripts/setup-public-hosting.sh
   ```

   The script creates the **separate** public Hosting site, or keeps it if it already exists. It does not edit IAM, deploy content, touch DNS or replace an existing site. Use the same Google account that owns the Firebase project.
3. In [GitHub Actions repository variables](https://github.com/jackwolf-alt/high-church-notices/settings/variables/actions), add **FIREBASE_PUBLIC_SITE_ENABLED** with value **true**. Keep the two existing authentication variables.
4. Run **Deploy Churchpress to Firebase Hosting** on **main**. The dashboard and public site each have a named deployment step. Once green, test **https://churchpress-public-833739660900.web.app**. Check pricing, enquiry links, example search and dashboard sign-in links.
5. In Firebase Console → Hosting, select the **churchpress-public-833739660900** site, then **Add custom domain → churchpress.co.uk**. Add the DNS records Firebase gives you in Fasthosts. These will be records for the root domain, commonly shown as `@` in DNS settings. Use Firebase's actual record types and values; do not guess the IP addresses.
6. Optionally add **www.churchpress.co.uk** to this new site and redirect it to **churchpress.co.uk** using Firebase's custom domain options. Apply only the DNS changes Firebase requests for that name.
7. Keep **dashboard.churchpress.co.uk** attached to the existing **high-church-notices** Hosting site and leave its CNAME alone. Preserve all email/MX and unrelated DNS records. If Fasthosts already serves a main website at the root, changing those root web records switches that website to Churchpress; check the existing records before doing so.
8. Wait for Firebase verification and HTTPS, then visit **https://churchpress.co.uk** and follow **Sign in** to verify both sites.

The public website does not use Firebase Authentication, so the root domain does not need adding as an authorised authentication domain just to serve these pages. The dashboard's authorised domain remains necessary. Both Hosting sites share the Firebase project's Hosting quotas.

## Content and maintenance

- Enquiry and free-trial buttons are `mailto:` links. To change the contact address, update **both** `public/index.html` and `public/privacy.html`, including their link text/subjects as appropriate. The email client opens only after the visitor selects a link; the website itself submits no enquiry form.
- Pricing and trial wording appears in the pricing card, FAQ and final call to action. Update all occurrences together when changing the offer. Agree payment arrangements and trial terms with new churches before onboarding; no billing or contractual cancellation promises have been invented on the website.
- The interactive example archive uses fictional notices. Search runs locally in `public/site.js`, without Firebase access, analytics or browser storage. Real church notices and credentials must never be added to public assets.
- The dashboard screenshot was captured from the actual app with intercepted Firebase responses and a synthetic local draft for **Example Parish Church**. It has no real account or weekly church data. The real notice sheet renderer and its Montserrat sizing are unchanged.
- The original Churchpress wordmark is extracted losslessly from the supplied brand kit. The embedded Manrope font is served locally and its full font licence is in `public/assets/FONT-LICENCES.txt`.
- The privacy page describes this public site's behaviour and email enquiries; it does not replace each church's privacy information for the dashboard. Update it when adding forms, analytics, payments or new handling of personal data.
- `public/robots.txt`, `public/sitemap.xml`, the canonical URL and social metadata use the final root domain.

App, public content and Hosting configuration changes trigger the existing workflow. Documentation-only changes do not deploy. For a rollback, use the release history of the **appropriate Hosting site**, then revert the corresponding GitHub change. Set `FIREBASE_PUBLIC_SITE_ENABLED` to `false` to stop future public-site deployments; it does not unpublish the site or stop dashboard deployments.

## Developer checks

Run `python3 tests/public_site_smoke.py` for responsive layout, navigation, mailto targets/pricing, local search, keyboard FAQ interaction, assets, and isolated staging. The tests use local HTTP and synthetic content only. Existing browser/PDF smoke tests verify the unchanged dashboard and sheet output. No application runtime dependencies or build system have been added.
