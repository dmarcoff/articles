# Mailgun run g3 (2026-10-29)

The "deep" shape of the lookup limit. In g2 every include sat at the top level ("wide"), and Gmail and
the Yahoo family passed 17 lookups and refused 22. A receiver could also cap how deep includes nest,
apart from the count. The cases of `experiments/spf-mailgun-depth` put Mailgun's include at the bottom
of a chain: `include:cNN.chain.mailpath.io` includes `c(NN-1)`, and so on down to `c01`, which holds
`include:_spf.mailgun.org`. They were sent once each through Mailgun's shared IPs to the same 19
GlockApps addresses as g2: 18 tracked seeds (5 Gmail, 2 Google Workspace, 3 Yahoo, 2 AOL, 1 AT&T,
2 Outlook, 2 Hotmail, 1 Apple) and GlockApps' monitor, which accepts every message. DKIM off. New
domains, so these reports don't mix with g2's.

Every Mailgun IP that sent this run is listed in `_spf1.mailgun.org`, so a receiver needs N+2 lookups
to reach the sender: N chain links, then `_spf.mailgun.org` and `_spf1.mailgun.org`. In a chain the
count grows with the depth, so the cases sit on both sides of what g2 showed for the count alone.

| Case | Record | Lookups to the sender | Sent (UTC) | GlockApps test |
|---|---|---|---|---|
| m19 | chain 15 links deep, Mailgun at the bottom | 17 | 14:16 | 2026-10-29-14:15:53:823t |
| m17 | chain 5 links deep | 7 | 14:17 | 2026-10-29-14:15:52:081t |
| m20 | chain 20 links deep | 22 | 14:18 | 2026-10-29-14:15:54:775t |
| m18 | chain 10 links deep | 12 | 14:19 | 2026-10-29-14:15:52:895t |

## Results

| Receivers | m17 (5 deep, 7) | m18 (10 deep, 12) | m19 (15 deep, 17) | m20 (20 deep, 22) |
|---|---|---|---|---|
| Gmail, Google Workspace (7) | accepted | accepted | accepted | 550 5.7.26 |
| Yahoo, AOL, AT&T (6) | accepted | accepted | accepted | 554 5.7.9 |
| Outlook, Hotmail (4) | accepted | 550 5.7.509 | 550 5.7.509 | 550 5.7.509 |
| Apple (1) | accepted | 554 5.7.1 | 554 5.7.1 | 554 5.7.1 |

- **Deep behaves like wide.** Gmail and the Yahoo family pass 15 nested levels (17 lookups) and
  refuse 20 (22 lookups), the same counts as in g2. No separate, stricter cap on depth showed; the
  refusal follows the total count.
- **Microsoft and Apple** accept the 5-link chain (7 lookups, within 10) and refuse from 12 lookups,
  as with the flat record.
- **The receivers' own headers agree.** On m19, the `Authentication-Results` written by Gmail (two
  seeds), Google Workspace, Yahoo, AOL and AT&T read `spf=pass` and `dmarc=pass` (checked in
  GlockApps' Header view on 2026-10-29).
- **Folders** as in g2: Gmail and Workspace inbox, the Yahoo family spam, Microsoft and Apple spam for
  m17, the only case they accepted.

## Files

As in `results/g2`: `events.csv`, `dns.json` (the case records and the 20 chain links),
`glockapps.csv` and `dmarc.csv` (`experiments/spf-mailgun-limit/results_g2g3.py`).

## DMARC aggregate reports

Google and Yahoo reported on 2026-10-30 and Microsoft (Outlook.com) on 2026-10-31, for every case
except that Yahoo's reports for m17 are missing. Yahoo's three reports for m17 (Yahoo, AOL, AT&T)
reached DMARKOFF but weren't processed: m17 was registered there as an unpaid domain, and DMARKOFF
drops the reports of unpaid domains without storing them. The SMTP answers above cover the same
messages.

- **Google and Yahoo pass up to 17 lookups,** nested or not: they record SPF `pass` for m17, m18 and
  m19.
- **Microsoft passes only m17** (7 lookups) and records SPF `permerror` and `reject` for m18, m19
  and m20, as for the flat records in g2.
- **m20 (22 lookups) is `reject`,** and Google, Yahoo and Microsoft all record SPF `permerror`. For
  the same count in a flat record (g2's m14), Google records `fail`.
