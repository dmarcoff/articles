# Who clicks the links in your emails: data

Data behind the GlockApps blog article *Who Clicks Your Email Links? A Test Across 130 Seeds*, which isn't published yet.

Between 16 and 19 November 2026 we sent 550 test emails in six runs: 544 to 130 GlockApps seeds at about 30 mailbox providers, five of the seeds spam-filter checks, and one per run to GlockApps' own authentication-check mailbox. Every link in every email carried its own token and pointed to `go.dmarcjet.com`, a host that logged every request, so each request named the email and the seed mailbox it came from. The question was which mail filters open the links in an email before the recipient does, when, with what, and whether they use up one-time links. This folder holds one row per email (where it landed and what happened to its links) and one row per request to the link host, with the networks named by ASN.

## Quick start

You need Python 3.13 (we ran 3.13.7); there are no dependencies.

```bash
cd who-clicks-email-links
python3 scripts/build_tables.py
```

It reads `data/messages.csv` and `data/requests.csv`, writes the four tables in [results/](results/) and prints the numbers quoted in the article, also saved in [results/summary.txt](results/summary.txt).

## How the test worked

- **The link host.** `go.dmarcjet.com` went live on 12 November 2026 at 20:09 UTC, with a new Let's Encrypt certificate, and logged every request with its headers, TLS handshake and the time to the millisecond. A page that loaded ran a small script (the beacon) that reported back the visit, including time on the page, mouse moves, keys, scrolls, clicks and whether the page was visible.
- **The emails.** Sent through Mailgun from `dmarcjet.com`, with SPF, DKIM and DMARC passing and Mailgun's click and open tracking off, so no link was rewritten on the way out. One email per seed mailbox and run, each with its own tokens. GlockApps' link checker was off for every test.
- **Placement.** GlockApps reported the folder of each email and how long it took to arrive (`glockapps_delay_s`). Mailgun's `delivered` event, the receiving server's 250 reply, is the zero for every time in `requests.csv`.
- **Our own requests** (from two addresses we used to check the host) are left out.

### The links

| Variant | Link | What it answers |
|---|---|---|
| V1 | A plain link to a page | Who opens links at all, when, with what |
| V2 | Three redirects on our host, then a page | Do they follow redirects, how far |
| V3 | One-time link used up by the first visit (GET) | Does a one-click confirmation survive |
| V4 | One-time link to a page with one button; only the button's POST uses it up | Do scanners press buttons |
| V5 | A hidden link (`display:none`), HTML part only | Any request is a robot |
| V6 | A link only in the plain-text part | Which part of the email they read |
| V7 | An image from our host | Who loads images, and when |
| V8 | A link with the token in the query string (`/q?t=…&src=digest`) | Are query strings kept |
| V9 | A bare host name as text, no link | Do they turn text into links, over http or https |
| V10 | One-time link whose page confirms by script as it loads, like a single-page app | Does a scanner that runs scripts trigger it |
| V11 | One-time link used up by the first visit, the token as the short last segment (`/k/<token>`) | Does a short token survive the scanner's rewriting |
| V12 | One-time link to a page with a form button, short token (`/v/<token>`) | Does the scanner press a button it can reach |
| V13 | One-time link to a page whose button confirms by script when clicked (`/j/<token>`) | Does the scanner click a scripted button |
| V14 | The footer "Unsubscribe" link of a newsletter, used up by the first visit (`/x/<token>`) | Does a scanner unsubscribe recipients |
| V15 | The `List-Unsubscribe` header's address, with `List-Unsubscribe-Post: List-Unsubscribe=One-Click`; a visit shows a button, only the one-click POST uses it up (RFC 8058) | Does anyone use the header's address |


### The runs

| Run | Sent (UTC) | Seeds | Email |
|---|---|---|---|
| l1 | 2026-11-16 06:09 to 06:16 | 131, the whole list | html (V1 to V10) or plain text, alternating within each provider |
| l2 | 2026-11-17 19:00 to 19:07 | 130, the whole list | the same with V11, html and text swapped |
| l3 | 2026-11-18 13:01 to 13:08 | 131, the whole list | as l2, swapped back |
| l4 | 2026-11-19 09:56 to 09:57 | 23, Microsoft groups only | html as l3; two Exchange mailboxes got a control email without any link, image or host name (`nolinks`) |
| l5 | 2026-11-19 10:17 to 10:18 | 7, Microsoft 365 business only | html with V12 and V13 added |
| l6 | 2026-11-19 12:03 to 12:10 | 128, the whole list | a short newsletter (`unsub`): V7, V1, V11, the footer link V14, and the `List-Unsubscribe` headers pointing at V15 |

The seed list is GlockApps' and changes slightly over time, so the runs that went to the whole list have 128 to 131 seeds.

## Files

### data/messages.csv

One row per email, 550 rows.

| Column | Meaning |
|---|---|
| `run` | l1 to l6 |
| `mailbox` | The seed mailbox: its GlockApps provider group and its place in that group's seed list, sorted by address (`Exchange (Office365) 3`). The same mailbox has the same name in every run while the seed list stays the same |
| `provider` | GlockApps' provider group (`Gmail (6 months+)`, `Exchange (Office365)`, `Microsoft (EOP)`…); `GlockApps auth check` is GlockApps' own monitoring mailbox |
| `format` | `html`, `text`, `nolinks` or `unsub` (see the runs) |
| `delivered_utc` | Mailgun's `delivered` event for the email; empty if Mailgun never reported one |
| `glockapps_placement` | `inbox`, `spam`, `other` (a tab) or `pending`; empty for GlockApps' five spam-filter seeds and its monitoring mailbox, which GlockApps reports without a placement |
| `glockapps_delay_s` | GlockApps' delivery time in seconds: the top `Received` header of the delivered email minus its `Date:` header |

### data/requests.csv

One row per request to the link host that carried an email's token: 987 rows, 17 of them Microsoft's requests to V8 whose rewritten query string had lost the token.

| Column | Meaning |
|---|---|
| `run`, `mailbox` | The email the token belongs to; empty for the V8 rows that lost their token |
| `variant` | V1 to V15 |
| `ms_after_delivery` | Milliseconds after Mailgun's `delivered` event for that email (after Mailgun accepted it, when there was no `delivered` event) |
| `method`, `scheme`, `status` | HTTP method, `http` or `https`, the host's answer |
| `kind` | `page` (the link itself or a rewritten form of it), `image` (V7), `stylesheet` and `beacon` (requests the page made), `noscript_pixel` |
| `note` | What the host recorded: `mutation` (the address was rewritten), `used_now` and `already_used` (a one-time link), `form`, `autopost_page`, `click_page`, `head_not_used`, `one_click` (the RFC 8058 POST body), `redirect_1` to `redirect_end`, `subresource_css`, `beacon`, `md` (a Markdown version), `query_rewritten` |
| `network` | ASN and owner of the address the request came from |
| `fetcher` | `microsoft_scanner` (AS8075), `google_image_proxy` (AS15169), `proton_image_proxy` (Proton's network), `glockapps_render` (GlockApps' own content analysis and report preview, AWS), `other` |
| `event` … `visibility` | Beacon rows only, as the page's script reported them: `load`, `t5` (5 s on the page) or `pagehide`; milliseconds on the page; mouse moves, keys, scrolls and clicks so far; page visibility |

We don't publish the clients' addresses, user agents, TLS fingerprints or browser environment (time zone, language, screen, hardware): a public list would help phishing pages show scanners a harmless page.

### data/background.csv

Who came to the host before the first email was sent, from the certificate (12 November 2026, 20:09 UTC) to the first send (16 November, 06:09 UTC), about 3.4 days: 3,089 connections and requests from 560 addresses in 102 networks, none with a token. Aggregated from the host's log, which isn't published.

| Column | Meaning |
|---|---|
| `category` | Sources that asked for our host name, by the first rule that fits: script-running browsers, phishing-kit check, AI crawlers, declared scanners, secret probes (`.env`, `.git`, SSH keys…), home page only, handshake only. Two more never used the name: "By IP, not by name" and the previous tenant's NAS devices still calling this IP address |
| `records` | Connections and requests |
| `ips`, `networks` | Distinct addresses and networks (ASN) |
| `first_seen_after_certificate` | First record after the certificate was issued |
| `main_networks` | The largest networks, by owner |

### results/

- [copies.csv](results/copies.csv): one row per email: the columns of `messages.csv`, then whether its links were opened (`opened_links`), by which fetcher, the first and last link request in seconds after delivery, the variants requested, whether page scripts ran, rewritten requests, the one-time links used up (`V11+24s`: V11, 24 s after delivery), whether the image was loaded and by whom, and every network that requested anything.
- [providers.csv](results/providers.csv): one row per run and provider group.
- [microsoft.csv](results/microsoft.csv): the five Exchange (Office365) mailboxes and the EOP mailbox across the six runs: format, links opened, GlockApps' delivery time.
- [microsoft-variants.csv](results/microsoft-variants.csv): for each link variant, over the emails Microsoft's scanner opened: how many carried it, requested it, requested it as sent or rewritten, and used it up.
- [summary.txt](results/summary.txt): the numbers quoted in the article.

## Screenshots

[screenshots/01-inbox-insight-microsoft-365-delivery-time.png](screenshots/01-inbox-insight-microsoft-365-delivery-time.png): GlockApps' report for run l5, Exchange (Office365): mailboxes 1, 3 and 5, whose links Microsoft's scanner opened, arrived in about two minutes; 2 and 4, which it didn't check, in 5 and 6 seconds. The seed addresses are replaced with the mailbox numbers of `microsoft.csv`.

## Caveats

- Seed mailboxes don't click. The data shows what filters do at delivery; checks at the time of a click, and whether links were rewritten in the delivered email, aren't in it.
- The Microsoft 365, EOP, Proofpoint and Barracuda seeds run their owners' policies; real organizations scan more or less. Five Exchange mailboxes and one EOP mailbox: the buttons (V12, V13) come from four scanned emails and the unsubscribe links (V14, V15) from two.
- `go.dmarcjet.com` was new, and the test emails were full of links, some of them hidden; an ordinary newsletter may draw fewer checks. The short newsletter of l6 was scanned in two of the six Microsoft 365 business mailboxes.
- The host log covers 12 November 2026, 20:09 UTC, to 22 November, 06:09 UTC, three to six days after each run; then the server was stopped. Every request with a token came within 86 seconds of delivery, and none came after 19 November, 12:10 UTC. A check after a longer gap isn't in the data.
- GlockApps' delivery time comes from the email's own headers (the top `Received` header minus `Date:`), so it isn't GlockApps' polling time, and it isn't the moment the email appeared in the mailbox either.

## How to cite

This folder:

> Markau, A., & DMARKOFF. (2026). *Who clicks the links in your emails: data* [Data set]. GitHub. https://github.com/dmarcoff/articles/tree/main/who-clicks-email-links

For licensing, see [License](../README.md#license) in the repository README.
