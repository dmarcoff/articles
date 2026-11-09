# Seed headers (g7)

Copied on 2026-11-06, about 07:50 UTC, from the Header view of GlockApps' web report. Tests: c03
2026-11-06-07:26:41:614t (our record first), c04 2026-11-06-07:26:42:306t (our record second). Seed
addresses reduced to their domain; Mailgun's VERP sender shown as `VERP`; lines rebuilt from the page
text, long values abridged as `…`.

Gmail, c03 (inbox). The DKIM signature is Mailgun's own, unaligned, so DMARC passed on SPF:

```
Authentication-Results: mx.google.com; dkim=pass header.i=@mailgun.org header.s=mg …;
    spf=pass (google.com: domain of VERP designates 159.135.228.62 as permitted sender) smtp.mailfrom=VERP;
    dmarc=pass (p=REJECT sp=REJECT dis=NONE) …
```

Google Workspace (`workspace-new-a.seed.example`), c03 (inbox): the same, `spf=pass` and
`dmarc=pass (p=REJECT sp=REJECT dis=NONE)`.

Outlook.com, c03 and c04 (spam, like the merged control); Hotmail, c04 (spam); Microsoft 365 seed
(`microsoft365-b.seed.example`), c03 and c04 (inbox). Every delivered copy read:

```
spf=pass (sender IP is …) smtp.mailfrom=c0N.cx.mailpath.io; … dmarc=pass action=none header.from=c0N.cx.mailpath.io
Received-SPF: Pass (protection.outlook.com: domain of c0N.cx.mailpath.io designates … as permitted sender)
```

(compauth=pass on the c03 copy where it was read.) The refused and bounced messages have no headers: Microsoft's reports say what it recorded.

Yandex (spam, like the merged control). One message per case:

```
c03  spf=softfail (mail-nwsmtp-mxfront-production-main-50: transitioning domain of c03.cx.mailpath.io does not designate …
c04  spf=pass (mail-nwsmtp-mxfront-production-main-979: domain of c04.cx.mailpath.io designates 159.135.228.15 as permitted …
```

Libero (spam), c03 and c04: only `Received-SPF: permerror`. GlockApps' SPF column says `pass`: not Libero's value. Virgilio not read.

ukr.net (spam), c03: the one receiver that names the cause.

```
Received-SPF: permerror (frv71.fwdcdn.com: multiple SPF records provided by c03.cx.mailpath.io) …
Authentication-Results: ukr.net; spf=permerror (multiple SPF records provided by c03.cx.mailpath.io) smtp.remote-ip=… ;
    dmarc=fail (p=reject sp=) header.from=…
```

Amazon WorkMail (inbox), c03:

```
Received-SPF: permerror (spfCheck: Error in processing SPF Record) client-ip=159.135.228.62; …
Authentication-Results: …; spf=permerror (spfCheck: Error in processing SPF Record) …; dmarc=temperror header.from=c03.cx.mailpath.io
```
