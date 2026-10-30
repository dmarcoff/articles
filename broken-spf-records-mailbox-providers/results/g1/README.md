# Mailgun run g1 (2026-10-23)

The 13 SPF cases of experiments/spf-mailgun, sent once each through Mailgun's shared IPs (US region)
to 44 GlockApps seeds (project 6): one per provider group, two for Gmail, Yahoo, AOL, Outlook and
Hotmail, plus GlockApps' own monitor. DKIM off except m00 (signed by Mailgun for m00.mailpath.io).

Before the run the case domains were warmed up on 2026-10-22 with correct SPF and Mailgun DKIM:
138 messages to the team's own mailboxes (`experiments/spf-mailgun/warmup.py`), all delivered except
one dead address. The DNS was switched to the case records at 06:17 UTC; `mailexp dns check` passed
79/79 before sending (`dns.json`). Bounce suppressions were cleared first.

| Case | Record | Sent (UTC) | GlockApps test |
|---|---|---|---|
| m08 | `include=_spf.mailgun.org` (unknown modifier) | 06:22 | 2026-10-23-06:21:06:724t |
| m00 | `include:_spf.mailgun.org`, Mailgun DKIM (control) | 06:24 | 2026-10-23-06:21:35:594t |
| m06 | include with no record, then Mailgun | 06:27 | 2026-10-23-06:21:36:376t |
| m12 | no record | 06:29 | 2026-10-23-06:21:37:109t |
| m11 | two records | 06:31 | 2026-10-23-06:21:37:869t |
| m10 | `ptr:mailgun.net` | 06:34 | 2026-10-23-06:21:38:645t |
| m03 | Mailgun, then 11 includes | 06:36 | 2026-10-23-06:21:39:709t |
| m09 | `includes:` (unknown mechanism) | 06:39 | 2026-10-23-06:21:40:468t |
| m04 | 3 void lookups, then Mailgun | 06:41 | 2026-10-23-06:21:41:182t |
| m07 | Mailgun, then an include with no record | 06:43 | 2026-10-23-06:21:41:983t |
| m05 | 2 void lookups, then Mailgun | 07:22 | 2026-10-23-07:22:45:795t |
| m02 | 11 includes, then Mailgun | 07:25 | 2026-10-23-07:22:46:601t |
| m01 | `include:_spf.mailgun.org` (control) | 07:27 | 2026-10-23-07:22:47:427t |

## Files

- `events.csv`: every Mailgun event for these messages (accepted, delivered, failed with the
  receiver's reply), matched to cases by Message-ID, recipients reduced to their domain
  (`experiments/spf-mailgun/events_csv.py`). Mailgun retries deferrals itself, for up to 8 hours.
  Re-pulled on 2026-10-25, so it holds the last retries too: Mailgun gave up on ukr.net's m06 and
  Interia's m09 and m12 after 8 hours (`602 Too old`, reason `old`). `reason` is Mailgun's own
  classification (`espblock`, `generic`, `old`), `enhanced_code` the receiver's enhanced status
  code and `provider` Mailgun's name for the recipient's provider.
- `dns.json`: the case records as public DNS served them before sending.
- `glockapps.csv`: per case and provider group, where the message landed and the SPF, DKIM and
  DMARC results GlockApps read from the seeds' headers (format and caveats as in `results/r1`: for
  Libero, Virgilio, Proton, T-Online, vodafone and freenet the SPF column is GlockApps' own value,
  not the receiver's).
- `headers.md`: seed header excerpts: Mailgun's own `d=mailgun.org` signature on m04, and the
  receivers' own SPF verdicts where GlockApps' summary shows something else (Libero, Virgilio,
  Proton, T-Online, vodafone and freenet on m02 and m12), with WorkMail, ukr.net (m02, m04, m10)
  and the two Outlook.com and Hotmail copies of m11 for comparison.
- `dmarc.csv`: the receivers' aggregate reports for the g1 mail (read 2026-10-25; La Poste and
  Zoho added 2026-10-30), dated as in `results/r1`. Google's rows come from its 2026-10-22 report
  for the cases sent before 07:00 UTC (Google's day follows Pacific time), told apart from the
  warm-up by the missing domain DKIM signature; m00's can't be told apart and are left out.
  Zoho's rows carry the date its reports state (2026-10-21, see below); m00's Zoho row also counts
  the w1 message of 2026-10-22 and is left out too.
- `bounce-classification.json`: what Mailgun's bounce classification report (its API, read
  2026-10-25) returns for the 13 domains: 89 critical bounces, all `ESPBLOCK`, under six provider
  labels.
- `suppressions.csv`: the bounce suppression list of each domain on 2026-10-25, empty for all
  13; the lists were cleared at 06:20 UTC on 2026-10-23, right before the run.
- `warmup-suppression.csv`: the only suppression seen: a warm-up address at freenet bounced
  (`550 unrouteable address`) from two domains on 2026-10-22, and Mailgun then refused to send to
  it from two others (`605 Not delivering to previously bounced address`).

## What the receivers did

Nothing was refused for the IP this time. Everyone delivered both controls (m00, m01) and the cases
that match before the problem (m03, m05, m07). For the rest (✓ accepted at SMTP, Mailgun's
"delivered"; ✗ refused; ⏸ kept deferring):

| Receiver | m02 lookups | m04 voids | m06 include, no record | m08 `include=` | m09 `includes:` | m10 ptr | m11 two records | m12 none |
|---|---|---|---|---|---|---|---|---|
| Gmail, Google Workspace | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Yahoo, AOL, att.net | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Outlook, Hotmail | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗, 2 of 6 ✓ | ✗ |
| Microsoft 365, EOP, Proofpoint seeds | ✗* | ✓ | ✗* | ✗* | ✗* | ✓ | ✗*, M365 ✓ | ✗* |
| Apple, GMX, web.de, mail.com | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Yandex, Mail.ru, Laposte, Zoho, mailo | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Onet, Barracuda filter | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Interia | ✗ at RCPT | ✓ | ✗ at RCPT | ✗ at RCPT | ⏸ | ✓ | ✗ at RCPT | ⏸ |
| naver | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| ukr.net | ✓ | ✓ | ⏸ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T-Online, freenet, vodafone, WorkMail, Seznam, Libero, Virgilio, Proton, SpamAssassin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

\* accepted at SMTP, then bounced: `550 5.7.509 Access denied, sending domain … does not pass DMARC
verification` (the Proofpoint seed delivers into Microsoft 365).

The refusals name DMARC: Gmail `5.7.26 Unauthenticated email … is not accepted due to domain's DMARC
policy`, Microsoft `5.7.509`, Yahoo/AOL `554 5.7.9 … failed authentication checks`, Apple `554
5.7.1 Your message was rejected due to …'s DMARC policy`, GMX/web.de `Reject due to sender domain's
DMARC policy`. Interia refuses at RCPT on SPF itself (`Rejected due to SPF with invalid content`).

What it says:

- **The 10-lookup limit (m02) is not enforced by Google or Yahoo**, the two largest US mailbox
  providers; Microsoft, Apple, GMX/web.de, Yandex, Mail.ru, Laposte, Onet, Interia, Zoho and mailo
  enforce it. Gmail's acceptance repeats the direct runs (p1, r1).
- **The void-lookup limit (m04)** is enforced by Onet and the Barracuda filter only, as in r1.
- **Two records (m11) give a coin toss** at Microsoft: 2 of 6 Outlook/Hotmail messages delivered,
  4 refused, from the same record. Yandex accepted s11 in r1 and refused m11 here. A receiver that
  picks the first record DNS returns gets a passing or failing record depending on the order.
- **naver refuses only an explicit `fail`** (m08) at SMTP when the IP has a reputation. The other
  failing cases it accepted never reached the seed (GlockApps placement below), so naver drops
  them instead; from our PBL-listed IP in r1 it refused every case without a pass.
- **ukr.net** again treats an include target without a record as a temporary error (m06).
- The same nine receivers accept everything, as with the direct runs: they don't refuse on DMARC at
  SMTP, so their verdicts come from the seeds' own headers and DMARC reports.

## Where the delivered messages went (GlockApps)

Through Mailgun the folder no longer hides SPF behind IP reputation: Gmail and Google Workspace put
every passing case in the inbox, m02 (11 lookups) included. Yahoo, AOL, att.net and Yandex put
everything in spam, Interia everything in its Offers tab.

The receivers that accept everything at SMTP:

- **T-Online and vodafone deliver every case to the inbox**, `fail` (m08) and no record (m12)
  included, and their headers record no SPF or DMARC result at all (T-Online's and vodafone's
  Authentication-Results carry only `dkim=none`, freenet's only `iprev`): nothing shows they act on
  `p=reject`. Freenet does the same except that m11 and m12 go to spam.
- **Amazon WorkMail** reports the permerror cases (m02, m06, m09, m11) as `dmarc=temperror` and
  delivers them to the inbox, but drops m08 (`fail`) and m12 (no record) after accepting them. It
  does apply the lookup limit: m02 is `permerror` there.
- **Seznam** delivers the passing cases to the inbox and drops the failing ones silently, and so
  does **naver**.
- **Italiaonline and Proton** put the failing cases and m02 in spam, as in the direct runs, with
  their own verdicts in the headers: Libero and Virgilio `Received-SPF: permerror` for m02 and m11,
  Proton `spf=fail` and `dmarc=fail` (GlockApps' SPF column says `pass` for m02).
- **ukr.net** puts the failing cases in spam, reports `permerror` for m04 (void lookups) and `fail`
  for m10 (ptr).

For m11 (two records), Microsoft delivered one of two Outlook and one of two Hotmail seeds, none of
Outlook.de and Outlook.fr, and the Microsoft 365 seed; every delivered copy reads `spf=pass`.

## DMARC aggregate reports

Google, Yahoo, GMX, WEB.DE, mail.com, Mail.ru, Seznam, Interia, Outlook.com, Microsoft 365, Zoho
and La Poste reported for the g1 mail, Amazon (for WorkMail) for one case. The last Outlook.com and
Microsoft 365 reports arrived on 2026-10-25, 34 to 41 hours after their window, and were added on
2026-10-26. Zoho's arrived on 2026-10-24 but were missed until 2026-10-30 because of their dates,
and La Poste's arrived on 2026-10-29, about 143 hours after the mail; both were added on 2026-10-30.
Both came after the test, which ended on 2026-10-23. The article counts Zoho as reporting only days
later and La Poste among the 12 of the 21 providers that sent no reports during the test; the rows
added here don't change that count.

- **Every verdict matches the SMTP and seed results** (La Poste's DMARC column aside, see below).
  Google, Yahoo and Seznam `pass` m02; GMX, WEB.DE, mail.com and Mail.ru report `permerror` and
  `reject`.
- **Mailgun's `mailgun.org/mg` signature** is on every m04 copy delivered to Gmail, Yahoo, AOL,
  AT&T, GMX, WEB.DE and mail.com (12 seeds, checked header by header) and on none of the other
  26. Google's and Yahoo's reports list it (Google's on half its copies: Gmail, not Workspace);
  GMX's, WEB.DE's and mail.com's reports don't mention it.
- **Microsoft reports what it refused.** Outlook.com's reports list the six messages it refused at
  SMTP for every failing case, with disposition `reject`; Microsoft 365's list the messages it
  bounced after accepting, except m08's three.
- **m11 (two records):** Outlook.com reports two messages `pass` and four `fail`, Microsoft 365 one
  `pass` and two `fail`: a `pass` for exactly the messages Microsoft delivered. Google, Interia and
  Microsoft label the failure `fail`; Yahoo, GMX, Mail.ru, Seznam, Zoho and La Poste `permerror`.
- **m09 (`includes:`):** Google `fail`, Mail.ru `none`, everyone else (Microsoft included)
  `permerror`.
- **m08 (`include=`):** `fail` everywhere, as RFC 7208 §6 implies for an ignored modifier, except at
  Outlook.com, which reports `permerror`.
- **Seznam** reports `reject` for the failing cases it accepted at SMTP, as in the direct runs.
- **La Poste and Zoho** report `reject` for exactly the six cases they refused at SMTP (m02, m06,
  m08, m09, m11, m12, all with 550 5.7.1), and both label SPF the same way: `permerror` for m02,
  m06, m09 and m11, `fail` for m08, `none` for m12.
- **La Poste's DMARC result reads `pass` on every row**, the six rejected ones included, while
  its SPF result says `permerror`, `fail` or `none` and its disposition `reject`. `dmarc.csv` keeps
  the value as reported; for La Poste, go by `spf_result` and `disposition`. Each report covers one
  message, with the window set to that message's time.
- **Zoho's reports state a window that ends before the mail they count**: 2026-10-21 07:00 to
  2026-10-22 07:00 UTC on every case, for mail sent from 2026-10-22 08:55 (w1, m00) to 2026-10-23
  07:28 UTC. Apart from w1's m00 message, these domains sent Zoho no other mail.

