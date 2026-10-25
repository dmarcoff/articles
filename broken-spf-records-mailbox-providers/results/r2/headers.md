# Seed headers (r2)

Copied on 2026-10-24 from the Header view of GlockApps' web report (project 6). Seed addresses
reduced to their domain.

## s02: 11 DNS lookups before `ip4`, Gmail seed (…@gmail.com, inbox)

Test 2026-10-23-08:01:44:452t, sent 2026-10-23 08:11:15 UTC.

```
Received-SPF: pass (google.com: domain of b-r2-s02-109-98cafe7879@s02.mailpath.io designates
    184.195.33.8 as permitted sender) client-ip=184.195.33.8;
Authentication-Results: mx.google.com; spf=pass (google.com: domain of
    b-r2-s02-109-98cafe7879@s02.mailpath.io designates 184.195.33.8 as permitted sender)
    smtp.mailfrom=b-r2-s02-109-98cafe7879@s02.mailpath.io;
    dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=s02.mailpath.io
```

Gmail evaluates the record that needs 11 lookups to `pass` and DMARC passes on SPF alone (the
message carries no DKIM signature).

## s02 at Libero, Virgilio and Proton

Copied on 2026-10-26 from the Header view; lines rebuilt from the parsed fields, abridged as `…`.
Test 2026-10-23-08:01:44:452t; all three filed the message in spam. GlockApps' SPF column says
`pass` for them.

Libero and Virgilio carry no Authentication-Results, only

```
Received-SPF: permerror
```

Proton:

```
Authentication-Results: mail.protonmail.ch; dmarc=fail … header.from=s02.mailpath.io
Authentication-Results: mail.protonmail.ch; spf=fail smtp.mailfrom=s02.mailpath.io
Authentication-Results: mail.protonmail.ch; arc=none …
Authentication-Results: mail.protonmail.ch; dkim=none
```

## s11 (two records) at Libero, Proton and Yandex

Test 2026-10-23-08:01:46:456t. Libero: `Received-SPF: permerror`. Proton: `spf=fail
smtp.mailfrom=s11.mailpath.io` and `dmarc=fail … header.from=s11.mailpath.io`, in separate
headers as for s02. Both in spam. Yandex (spam, like its controls):

```
Authentication-Results: mail-nwsmtp-mxfront-production-main-69…; spf=pass (mail-nwsmtp-mxfront-production-main-69:
    domain of s11.mailpath.io designates 184.195.33.8 as permitted sender, …) …
```

The same three gave the same verdicts in r1 (`results/r1/headers.md`), while GlockApps' SPF column
switched from `pass` in r1 to `permerror` here.
