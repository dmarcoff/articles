# Pilot p1 (2026-10-21)

Three cases of the SPF experiment, sent once, to check the whole chain before the full runs.

| Case | Record | DKIM | Sent (UTC) | GlockApps test |
|---|---|---|---|---|
| s00 | `v=spf1 ip4:184.195.33.8 -all` | yes | 19:29–19:36 | 2026-10-21-19:27:40:073t |
| s02 | 11 includes, then `ip4:184.195.33.8 -all` | no | 19:36–19:44 | 2026-10-21-19:27:41:736t |
| s01 | `v=spf1 ip4:184.195.33.8 -all` | no | 19:44–19:51 | 2026-10-21-19:27:40:878t |

Order: control, case under test, control. Each case went to the same 111 GlockApps seed addresses
(GlockApps project 6), marker in `X-API-Campaign-id`, 3 s between recipients, from 184.195.33.8
(PTR `mta.mailpath.io`). Deferred messages were retried at 19:53 and 20:04 with `mailexp retry`;
all 13 were accepted on the second attempt.

## Files

- `smtp.csv`: every delivery attempt, one row each, with the receiver's reply. Recipient addresses are
  reduced to their domain and masked inside replies; the seed list itself is not published.
- `glockapps.csv`: per provider group and case, the delivered messages, their folder and the SPF, DKIM
  and DMARC results GlockApps reported (`-` = not reported). Taken at 20:09 UTC; Yahoo, Microsoft and the
  other blocked receivers have no rows because nothing reached them. The SPF column is not the
  receiver's verdict for Libero, Virgilio and Proton: see below.
- `dns.json`: what public DNS (1.1.1.1) served for every record of the experiment right before sending.
- `headers.md`: what Libero, Virgilio and Proton wrote into their headers for s02.

The raw send log (with seed addresses) is kept on the sending host and in the gitignored `runs/p1/`.

## What it showed

**The IP decides first.** 59 of the 111 seeds refused the IP itself in every case, before SPF could
matter: Microsoft (Outlook, Hotmail, Office 365 tenants) and Apple via Spamhaus, Yahoo/AOL/att
(`TSS09 … permanently deferred`), GMX/web.de/mail.com, freenet, T-Online, vodafone, Zoho and Amazon
WorkMail via their own lists. Spamhaus lists the whole 184.192.0.0/10 in the PBL, has suspended
automatic removal for it, and states that removal "is not allowed by the IP netblock owner's policy"
(lookup on spamhaus.org, 2026-10-22). Correct rDNS doesn't change that, so the experiment keeps the IP
and reports the blocking.

**s02 exceeds the 10-lookup limit, and receivers split:**

| Behaviour | Receivers |
|---|---|
| Refuse at RCPT on SPF itself (`Rejected due to SPF with invalid content`) | Interia |
| Refuse after DATA on DMARC (permerror → DMARC fail → `p=reject`) | Mail.ru, Yandex, Laposte, Onet, naver, mailo |
| Accept with `spf=pass`, `dmarc=pass` | Gmail, Google Workspace, ukr.net |
| Accept with `spf=pass`, to spam like the unsigned control s01 | Seznam |
| Accept to spam with `Received-SPF: permerror`, where the unsigned control s01 went to the inbox | Virgilio, Libero |
| Accept to spam with `spf=fail` and `dmarc=fail` | Protonmail |

For Gmail the verdict doesn't rest on GlockApps' reading alone: under `p=reject` with no DKIM, Gmail
accepting the message at DATA means its DMARC check, and so its SPF check, passed. For Proton and
Italiaonline (Virgilio, Libero) GlockApps showed `spf=pass`, which sat badly with what they did with
the message. Their raw headers, checked on 2026-10-25, settle it: Libero and Virgilio write only
`Received-SPF: permerror`, Proton writes `spf=fail` and `dmarc=fail` in separate
Authentication-Results headers. Both enforce the lookup limit; GlockApps' SPF value for them is its
own, not theirs. Seznam
foldered by DKIM: the signed control s00 reached the inbox, both unsigned cases went to spam.
SpamAssassin scored s02 at 3 and both controls at 0.

**Placement is not the signal at Google.** Gmail and Google Workspace put every message in spam, the
SPF + DKIM control included: a new IP and new domains. Compare their authentication results, not the
folder. Mail.ru, Laposte, Onet, ukr.net, Proton and mailo delivered the controls to the inbox.

**Temporary refusals.** Interia greylists (451 on the first try), and Gmail rate-limits new SPF domains
(`421 4.7.28 … unusual rate of mail originating from your SPF domain`). Both accepted on retry, which
is why `mailexp retry` exists.

## DMARC aggregate reports

`dmarc.csv`: what the receivers themselves reported for s00–s02 (rua to DMARKOFF, re-read on
2026-10-25). Only Google, Seznam and Mail.ru sent reports for these messages. `report_date` is the date DMARKOFF gives the report: the UTC date its window starts. Seznam's
window runs 22:00–22:00 UTC, so its report for a day's mail is dated the day before. Google's
report says 00:00–23:59 UTC but follows Pacific time: mail sent before 07:00 UTC lands in the
previous day's report.

- Google and Seznam report **`spf=pass`** for s02, the record that needs 11 DNS lookups. Google's
  own report confirms what its acceptance at DATA implied; Seznam's settles that its spam placement
  of the unsigned cases had other reasons.
- Mail.ru reports **`spf=permerror`** for s02 and the disposition `reject`, matching its SMTP refusal.
- Google's message counts run above what we sent (31 for 26 messages in s01, which had 5 deferrals
  retried): it counts deferred attempts too. Its 39 for s02 also holds the first r1 messages, sent
  at 06:57 UTC the next morning (Pacific time). Quote the verdicts, not the counts.

## Still open

- One pilot is one observation; the full runs repeat every case three times.
