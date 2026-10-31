# Mailgun run g4 (2026-10-31)

A CNAME next to a TXT record at the same name, the two leading to different SPF records. Some
customers' Return-Paths look like this: one ESP's CNAME and another ESP's SPF record at the same
name, sometimes with an MX too, and DMARKOFF's monitoring saw the stored record flip between the
two. RFC 1034 3.6.2 forbids a CNAME next to other data, but some DNS providers publish it. The run
asks which record receivers evaluate when the MAIL FROM domain is such a name.

Route 53 refuses such a zone, so the case names live in `cx.mailpath.io`, delegated to `authdns` on
our host (184.195.33.8). It answers the way the zone in the ticket was served: a TXT or MX query gets
the name's own records, a type the name lacks (A, AAAA, NS, SOA, and MX where the name has none) gets
the CNAME alone, and the server never follows the CNAME itself. It logs every query, which shows
which name each receiver's resolver asked for TXT. Every record has a TTL of 300 s. The CNAME
targets carry an A record (184.195.33.8) and Mailgun's MX, so a receiver that checks that the sender
domain resolves gets an answer through the CNAME.

The cases of `experiments/spf-cname-txt` were sent once each through Mailgun's shared IPs (US region)
to the 45 GlockApps addresses of g1 (project 6): 44 tracked seeds, one per provider group, and
GlockApps' monitor, which accepts every message. MAIL FROM and From are the case domain, DKIM is
off and the DMARC policy is `p=reject`, so DMARC rests on SPF. "passes" below is
`v=spf1 include:_spf.mailgun.org -all`, "fails" is `v=spf1 -all`.

| Case | Own TXT at the name | CNAME target's TXT | MX at the name | Sent (UTC) | GlockApps test |
|---|---|---|---|---|---|
| c04 | passes | fails | no | 10:55 | 2026-10-31-10:50:29:555t |
| c01 | passes | no CNAME (control) | yes | 10:58 | 2026-10-31-10:49:56:091t |
| c03 | passes | fails | yes | 11:00 | 2026-10-31-10:50:28:546t |
| c06 | fails | passes | no | 11:03 | 2026-10-31-10:50:31:147t |
| c05 | fails | passes | yes | 11:05 and 11:17 | 2026-10-31-10:50:30:342t |
| c02 | none, CNAME only (control) | passes | no | 11:07 | 2026-10-31-10:50:27:384t |

The pairs mirror each other. A receiver that accepts c03 and refuses c05 read the name's own record;
one that refuses c03 and accepts c05 read the target's. c04 and c06 have no MX at the name, so a
receiver that checks the sender domain's MX before SPF gets the CNAME there, and its resolver holds
it when SPF asks for TXT. c02 is how ESPs usually set up a Return-Path, a CNAME alone.

## How the run went

- Mailgun verified the six domains while they had plain records (`mailexp dns zone --phase verify`).
  The zone was switched to the case records at 10:49:24 UTC, and sending started at 10:55:30, after
  the 300-second TTL of the verification records had run out.
- Mailgun re-checks domains on its own. During c05's send its check read c05's and c06's own record
  (`v=spf1 -all`) and marked both domains unverified, and its API refused 22 of c05's 45 messages
  ("The domain is unverified and requires DNS configuration"). c06 had been sent in full just
  before. The ESP met the same ambiguity as the receivers.
- To complete c05, its name got the plain Mailgun record without the CNAME from 11:11:59 to
  11:12:20 UTC, Mailgun verified it, and the case records came back. After five minutes the 22
  remaining seeds were sent, at 11:17:31 to 11:17:59. c05's queries inside that window are left out
  of `queries.csv` and of the tables below; no c05 message was in flight then.

## Results

Mailgun's log, all 45 addresses per case (GlockApps' monitor and the spam-filter probes included):

| | c01 | c02 | c03 | c04 | c05 | c06 |
|---|---|---|---|---|---|---|
| accepted | 45 | 45 | 37 | 31 | 19 | 25 |
| refused | 0 | 0 | 8 | 14 | 26 | 20 |

Per receiver, what it answered at SMTP and, from authdns's log, which record its resolvers fetched
(`matrix.txt`, `dnslog.txt`). Where a receiver accepts everything at SMTP, the folder and the
verdicts it wrote into the seed's headers come from GlockApps.

| Receiver | Record it reads | c03 | c04 | c05 | c06 |
|---|---|---|---|---|---|
| Gmail, Google Workspace, Google filter probe (6) | own | accepted | accepted | 550 5.7.26 | 550 5.7.26 |
| Yahoo, AOL, AT&T (5) | own | accepted | accepted | 554 5.7.9 | 554 5.7.9 |
| La Poste | own | accepted | accepted | 550 5.7.1 | 550 5.7.1 |
| Zoho, Naver, mailo | own | accepted | accepted | 550 5.7.1 (mailo 550) | 550 5.7.1 (mailo 550) |
| Barracuda filter probe | own (by its answers; resolvers not identified) | accepted | accepted | 550 blocked | 550 blocked |
| ukr.net | own | inbox | inbox | spam, `spf=fail` | spam, `spf=fail` |
| Amazon WorkMail | own | inbox | inbox | accepted, not in the mailbox | accepted, not in the mailbox |
| Mail.ru | target | 550 5.7.1 | 550 5.7.1 | accepted | accepted |
| Yandex | target | spam, `spf=fail` | 550 5.7.1 | spam, `spf=pass` | spam, `spf=pass` |
| Proton | both; DMARC follows the target | spam, `dmarc=fail` | spam, `dmarc=fail` | inbox, `dmarc=pass` | inbox, `dmarc=pass` |
| Outlook.com, Hotmail (6) | mostly target, split | 4 × 550 5.7.509, 2 accepted | 3 × 550 5.7.509, 3 accepted | 1 × 550 5.7.509, 5 accepted | accepted |
| Microsoft 365 tenants (3) | mostly target, split | 550 5.7.509 | 550 5.7.509 | 2 × 550 5.7.509, 1 accepted | accepted |
| Interia | own with an MX, target without | Offers tab | 550 5.7.1 | 550 5.7.1 | Offers tab |
| Onet | own with an MX, target without | inbox | 550 5.7.23 (SPF fail) | 550 5.7.23 | 554 5.7.1, no reason given |
| freenet | own with an MX, target without | inbox | deferred (457), then spam | deferred (457), then spam | inbox |
| GMX, web.de, mail.com (4) | own with an MX, split without | accepted | 3 × 554, 1 accepted | 554 | 2 × 554, 2 accepted |
| Libero, Virgilio | own with an MX, split without | inbox | inbox and spam | spam | spam |
| Apple iCloud | own with an MX, unsteady without | spam | 554 5.7.1 | 554 5.7.1 | 554 5.7.1 |
| Seznam | both | inbox | inbox | inbox | inbox |
| Vodafone, T-Online | no SPF check | inbox | inbox | inbox | inbox |

c01 and c02 were accepted by every receiver. A CNAME alone is fine; the trouble is a CNAME next to
the name's own records.

- **The same message passes SPF at some receivers and fails at others, whichever record is the
  right one.** With the name's own record correct (c03, c04), Mail.ru and most of Microsoft's seeds
  refuse the mail, and without an MX at the name Yandex, Interia, Onet, GMX, web.de and Apple do too.
  With the target's record correct (c05, c06), Gmail, Google Workspace, the Yahoo family, La Poste,
  Zoho, Naver, mailo, Apple and the Barracuda filter refuse it.
- **Gmail and the Yahoo family read the name's own record.** Their resolvers ask the name for TXT
  before anything else. Yahoo's asked the name for TXT even after an MX or SOA query had returned
  the CNAME.
- **Mail.ru, Yandex and Microsoft resolve the domain's A record first,** get the CNAME and then ask
  its target for TXT. Microsoft's seeds split within a single case, so which record a given
  Microsoft server reads depends on the state of its resolver's cache.
- **An MX at the name decides for Interia, Onet, freenet, GMX, web.de, mail.com and Italiaonline.**
  With one, they read the name's own record (c03, c05). Without one, their MX query returns the
  CNAME and SPF then reads the target (c04, c06): every time at Interia, Onet and freenet, for some
  seeds at the others. Apple read the target in c04 and its own record in c06, though the
  two cases are laid out the same.
- **Some outcomes don't show at SMTP.** ukr.net and freenet file the failing message in spam.
  Amazon WorkMail accepted c05 and c06 at SMTP, and neither had reached the mailbox by 11:40 UTC. Proton's resolvers fetched both records; its DMARC result
  followed the target's.
- **Vodafone never asked for TXT**, so it doesn't evaluate SPF. T-Online records no SPF result either
  (`results/r1`).

## What GlockApps showed

- The authentication summary of c05 and c06 reads `spf: pass` and `dmarc: pass`, taken from the
  seeds that received the message; 26 and 20 refused at SMTP. c05's verdict is "Still incomplete",
  with 27 of 44 seeds not received.
- None of its flags names the cause. The top issues are DKIM_AUTH_NONE, DMARC_DELIVERY_ISSUE, the
  spam-folder flags and, for c06, IP_IN_BLOCKLIST.
- Its SPF column shows `pass` in every case for freenet, T-Online, Vodafone, Libero, Virgilio and
  Proton: for them it is GlockApps' own value, not the receiver's (`results/r1`). freenet filed c04
  and c05 in spam, and Proton's own DMARC header says `fail` for c03 and c04.
- WorkMail's undelivered c05 and c06 show as "pending", the same as a refusal.

## Files

- `events.csv`: every Mailgun event for these messages, as in `results/g1`
  (`experiments/spf-mailgun/events_csv.py`), recipients reduced to their domain.
- `queries.csv`: authdns's log for the case names (the name, its CNAME target and its DMARC record;
  not Mailgun's DKIM and tracking names) from 10:55 to 11:40 UTC, with the resolver's AS from Team
  Cymru's DNS service. c05's re-verification window is left out.
- `dnslog.txt`: per case and resolver network, the order of its queries ("A name>cname" is the
  CNAME, "TXT target>data" the target's record), and the SMTP outcomes
  (`experiments/spf-cname-txt/dnslog.py`).
- `matrix.txt`: receiver group by case, the SMTP outcome and which TXT the group's resolvers fetched
  (`experiments/spf-cname-txt/matrix.py`).
- `dns.json`: the case zone as authdns served it, checked with
  `mailexp dns check --resolver 184.195.33.8:53` at 10:49:37 UTC, right after the switch.

The GlockApps results are summarized above; the tests are listed in the case table.

## DMARC aggregate reports

The six domains were added to DMARKOFF (project 1012) as paid before sending, so no report is lost
the way Yahoo's for m15 and m17 were (`results/g2`, `results/g3`). Google and Yahoo are due on
2026-11-01, Microsoft about 2026-11-02. Google's day follows Pacific time, so this mail is in its
2026-10-31 report. The zone stays delegated until the reports are in.

## Caveats

- One message per case and seed. Resolver caches change from minute to minute, so the receivers that
  split here could fall differently in another run.
- Resolvers are tied to receivers by their AS and by timing. Microsoft's consumer and business mail
  share an AS, as do GMX, web.de and mail.com (IONOS); Google's resolvers also serve the Google
  Workspace seeds and the Google filter probe.
- The three Microsoft 365 tenants are GlockApps' Microsoft 365, Microsoft EOP filter and Proofpoint
  filter seeds; all three have their MX at Exchange Online.
- Onet refused c06 after DATA with "554 5.7.1 Rejected" and no reason, though its resolver read the
  target's passing record.
