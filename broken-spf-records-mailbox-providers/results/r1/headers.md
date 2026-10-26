# Seed headers (r1)

Copied from the Header view of GlockApps' web report (project 6). Seed addresses reduced to their
domain; lines rebuilt from the parsed header fields, with long values abridged as `…`.

## s02: 11 DNS lookups before `ip4`

Test 2026-10-22-06:56:09:140t, checked on 2026-10-25. Libero and Virgilio (spam) write only
`Received-SPF: permerror`; Proton (spam) writes `spf=fail` and `dmarc=fail` in separate
Authentication-Results headers. GlockApps' SPF column says `pass` for all three.

## s11: two records

Test 2026-10-22-08:20:39:805t, checked on 2026-10-26. Libero (spam):

```
Received-SPF: permerror
```

Proton (spam):

```
Authentication-Results: mail.protonmail.ch; dmarc=fail … header.from=s11.mailpath.io
Authentication-Results: mail.protonmail.ch; spf=fail smtp.mailfrom=s11.mailpath.io
Authentication-Results: mail.protonmail.ch; arc=none …
Authentication-Results: mail.protonmail.ch; dkim=none
```

Yandex (spam, like its controls):

```
Authentication-Results: mail-nwsmtp-mxfront-production-main-91…; spf=pass (mail-nwsmtp-mxfront-production-main-91:
    domain of s11.mailpath.io designates 184.195.33.8 as permitted sender, …) …
```

GlockApps' SPF column shows `pass` for Libero and Proton in this run and `permerror` in r2; their
own headers give the same failure in both runs.
