# Mailgun run g6 (2026-11-04)

Does an aligned DKIM signature rescue a message that fails SPF, and does the `all` qualifier decide
whether it gets the chance? RFC 9989 section 7.1 warns that `-all` can get a message rejected early in
the SMTP transaction, before DMARC runs, so a message that would pass on an aligned signature can be
lost. In g5 Naver, Interia and Onet refused `-all` citing SPF, but g5 sent no signed mail.

The cases of `cases/spf-all-dkim.yaml` keep g5's records and domains, with Mailgun signing for the From
domain, so the signature is the one change to them. `m00` is the control, passing SPF and DKIM. They
were sent once each through Mailgun's shared IPs to 9 GlockApps addresses: Onet 2, Interia 3, Naver 1,
Gmail 1 and Outlook.com 1 as a reference, and GlockApps' monitor, which accepts every message. Mailgun
had marked m21 to m23 unverified since g5, so they got their verification records first and the case
records last. The case records went live at 12:01:49 UTC and every domain stayed active throughout.

| Case | Record | Result for our sender | Sent (UTC) | GlockApps test |
|---|---|---|---|---|
| m22 | `v=spf1 ip4:192.0.2.1 ~all` | softfail | 12:07:18 | 2026-11-04-12:00:01:685t |
| m00 | `v=spf1 include:_spf.mailgun.org -all` | pass (control) | 12:07:46 | 2026-11-04-11:59:59:558t |
| m23 | `v=spf1 ip4:192.0.2.1 ?all` | neutral | 12:08:14 | 2026-11-04-12:00:02:736t |
| m21 | `v=spf1 ip4:192.0.2.1 -all` | fail | 12:08:42 | 2026-11-04-12:00:00:570t |

## Results

| Receiver (seeds) | m00 control | m21 `-all` | m22 `~all` | m23 `?all` |
|---|---|---|---|---|
| Onet (2) | inbox | 550 5.7.23 at RCPT | inbox | inbox |
| Interia (3) | Offers tab | 550 5.7.1 at RCPT | 451 4.4.0 at RCPT, 7 times, then 602 Too old | same |
| Naver (1) | inbox | 250, spam | inbox | inbox |
| Gmail (1) | inbox | inbox | inbox | inbox |
| Outlook.com (1) | inbox | spam | spam | spam |

- **Onet is the case RFC 9989 warns about.** It refused `-all` at RCPT with `SPF fail - not authorized`,
  before the message or its signature is sent, on both seeds. The same mail under `~all` and `?all`
  reached the inbox, with DMARC passing on DKIM. In g5, without a signature, it refused those two with
  a plain `554 5.7.1 Rejected`.
- **Interia answered before it could see the signature.** As in g5, it refused `-all` and deferred the
  other two with `Deferred due to SPF unsafe`, at RCPT. Mailgun retried for eight hours and gave up
  with `602 Too old` at 20:13 UTC. None of the nine messages was accepted, while the control reached
  the Offers tab on all three seeds.
- **Naver's g5 refusal wasn't an early one.** It accepted all three: `-all` went to spam and the other
  two to the inbox, with DMARC passing on DKIM. So its reply `Sender rejected because SPF check failed`
  in g5 doesn't mean it stops at SPF.
- **Gmail delivered all three to the inbox,** and Outlook.com all three to spam, with the control in the
  inbox. Outlook.com's headers show that authentication passed, so that folder came from its filter.
  It was one mailbox, and the control domain has a longer history, so this doesn't show why.
- **The predictions in `cases/spf-all-dkim.yaml`, written before sending:** Interia unchanged and Onet
  letting `~all` through were right. Naver still refusing `-all` was wrong.

## Headers

Read in GlockApps' Header view on 2026-11-04 and 2026-11-05. These are the receivers' own lines, which
agree with GlockApps' values for this run.

| Case | Receiver | SPF | DKIM | DMARC | Other |
|---|---|---|---|---|---|
| m21 | Naver | fail | pass | pass | spam folder |
| m22 | Naver | softfail | pass | pass, `p=REJECT`, `dis=NONE` | inbox |
| m23 | Naver | neutral | pass | pass, `p=REJECT`, `dis=NONE` | inbox |
| m21 | Gmail | fail | pass for m21 and for mailgun.org | pass | inbox |
| m22 | Onet | softfail | pass, `d=m22.mailpath.io` | pass, `p=reject`, applied disposition none | inbox |
| m23 | Onet (both seeds) | neutral | pass, `d=m23.mailpath.io` | pass, `p=reject` | inbox |
| m21, m22, m23 | Outlook.com | fail, softfail, neutral | pass, own domain | pass, `action=none` | `compauth=pass reason=100`, SCL 5, spam folder |

## Files

As in `results/g5`: `events.csv`, `dns.json`, `glockapps.csv` and `dmarc.csv`, the last two read on
2026-11-05. GlockApps' per-group rows cover all 8 tracked seeds here.

## DMARC aggregate reports

Read in DMARKOFF on 2026-11-05. Google's report for m22 (received 2026-11-05) and Outlook.com's
(received 2026-11-06) were read on 2026-11-09. Onet and Naver sent no reports in g4 or g5 either.

| Reporter (messages per case) | m00 | m21 `-all` | m22 `~all` | m23 `?all` |
|---|---|---|---|---|
| Google (1) | SPF pass | SPF fail | SPF softfail | SPF neutral |
| Outlook.com (1) | SPF pass | SPF fail | SPF softfail | SPF neutral |
| Interia (3) | SPF pass | no row | no row | no row |

- **Every row reads DKIM `pass` on the case's own domain, DMARC `pass` and disposition `none`, with no
  policy override.** Google's rows also carry Mailgun's `d=mailgun.org` signature with a `pass`.
- **Interia reported only the control,** having answered the other three at RCPT. Its report came 3.1
  hours after the window, and none came for m21 to m23, well past its longest wait of 5 hours. That
  fits RFC 9989 section 7.1: a refusal before DMARC runs doesn't appear in an aggregate report.
- **Dates.** Every report is dated 2026-11-04. Google's day follows Pacific time, and this mail fell on
  2026-11-04 there too.
