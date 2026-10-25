# Seed headers (g1)

Copied on 2026-10-24 from the Header view of GlockApps' web report (project 6). Seed addresses
reduced to their domain.

## m04: Mailgun's own DKIM signature

Test 2026-10-23-06:21:41:182t, sent with `o:dkim=no`, so the domain's own signature is absent.
Mailgun still signs mail for Gmail, the Yahoo family (Yahoo, AOL, AT&T) and United Internet
(GMX, WEB.DE, mail.com) with `d=mailgun.org; s=mg`, covering its `X-Feedback-Id` header
(feedback loops). Checked seed by seed on 2026-10-25: present and passing on all 12 such
seeds of m04, absent on the other 26 delivered copies (Google Workspace, Microsoft, Apple,
WorkMail, Zoho, Proton, Seznam, La Poste, freenet, T-Online, vodafone, Libero, Virgilio,
Interia, ukr.net, Mail.ru, Yandex, Naver, mailo). The signature passes but isn't aligned with
m04.mailpath.io; DMARC passes on SPF.

Gmail (…@gmail.com, inbox):

```
Authentication-Results: mx.google.com; dkim=pass header.i=@mailgun.org header.s=mg header.b="PL5/Peaf";
    spf=pass (google.com: domain of bounce+47ce29.d10d6e-…=gmail.com@m04.mailpath.io designates
    159.135.228.59 as permitted sender) smtp.mailfrom="bounce+47ce29.d10d6e-…=gmail.com@m04.mailpath.io";
    dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=m04.mailpath.io
DKIM-Signature: a=rsa-sha256; v=1; c=relaxed/relaxed; d=mailgun.org; q=dns/txt; s=mg; …
    h=Content-Transfer-Encoding: Content-Type: MIME-Version: Message-ID: Date: Subject: Subject:
    To: To: From: From: X-Feedback-Id: Sender; …
X-Feedback-Id: test@m04.mailpath.io::6ad9cc3d94235c9ae833a68d:mailgun
X-Mailgun-Dkim: false
```

Yahoo (…@yahoo.com, spam):

```
Authentication-Results: mta.yahoo.com; dkim=pass header.i=@mailgun.org header.s=mg
    arc_overridden_status=NOT_OVERRIDDEN; spf=pass smtp.mailfrom=m04.mailpath.io
    arc_overridden_status=NOT_OVERRIDDEN; dmarc=pass(p=REJECT) header.from=m04.mailpath.io
    arc_overridden_status=NOT_OVERRIDDEN;
DKIM-Signature: a=rsa-sha256; v=1; c=relaxed/relaxed; d=mailgun.org; q=dns/txt; s=mg; …
X-Mailgun-Dkim: false
```

Outlook (…@outlook.com, inbox): no Mailgun signature.

```
Authentication-Results: mx.microsoft.com 1; spf=pass (sender IP is 159.135.228.59)
    smtp.mailfrom=m04.mailpath.io; dkim=none (message not signed) header.d=none;dmarc=pass
    action=none header.from=m04.mailpath.io;compauth=pass reason=100
X-MS-Exchange-Organization-SCL: 1
X-Mailgun-Dkim: false
```

## m02 and m12: verdicts GlockApps' summary doesn't show

Copied on 2026-10-26 from the Header view. GlockApps' SPF column shows `pass` on m02 for Libero,
Virgilio, Proton, T-Online, Vodafone and freenet; their own headers say otherwise, or nothing.
WorkMail's and ukr.net's results, which GlockApps reads correctly, are here for comparison. The
lines are rebuilt from the parsed header fields, with long values abridged as `…`.

m02 (11 includes before Mailgun's include), test 2026-10-23-07:22:46:601t.

Libero and Virgilio (spam): no Authentication-Results at all, only

```
Received-SPF: permerror
```

Proton (spam): four separate Authentication-Results headers

```
Authentication-Results: mail.protonmail.ch; dmarc=fail (p=reject dis=none) header.from=m02.mailpath.io
Authentication-Results: mail.protonmail.ch; spf=fail smtp.mailfrom=m02.mailpath.io
Authentication-Results: mail.protonmail.ch; arc=none smtp.remote-ip=159.135.228.63
Authentication-Results: mail.protonmail.ch; dkim=none
```

Amazon WorkMail (inbox):

```
Received-SPF: permerror (spfCheck: Error in processing SPF Record) …
Authentication-Results: amazonses.com; spf=permerror (spfCheck: Error in processing SPF Record) …;
    dmarc=temperror header.from=m02.mailpath.io
```

ukr.net (inbox), which evaluates past the limit like Gmail:

```
Received-SPF: pass (frv71.fwdcdn.com: domain of m02.mailpath.io designates 159.135.228.63 as permitted sender) …
Authentication-Results: ukr.net; spf=pass (domain of m02.mailpath.io designates 159.135.228.63 as
    permitted sender) smtp.mailfrom=m02.mailpath.io; dmarc=pass header.from=…@m02.mailpath.io
```

T-Online, Vodafone and freenet (inbox): no SPF or DMARC result anywhere in the headers

```
T-Online   Authentication-Results: mailin45.t-online.de; dkim=none; dkim-atps=neutral
           Authentication-Results: mailin45.aul.t-online.de; dkim=none; dkim-atps=neutral
Vodafone   Authentication-Results: mx5.vodafonemail.de/…; dkim=none; dkim-atps=neutral
freenet    Authentication-Results: freenet.de; iprev=pass (v563.v524e8ec4.use4.send.mailgun.net)
               smtp.remote-ip=159.135.228.63
```

m12 (no record), test 2026-10-23-06:21:37:109t, looks the same at these three: T-Online's and
Vodafone's Authentication-Results carry only `dkim=none; dkim-atps=neutral`, freenet's only
`iprev=pass`.

## m04 and m10 at ukr.net

m04 (three void lookups, spam), test 2026-10-23-06:21:41:182t:

```
Received-SPF: permerror (frv72.fwdcdn.com: DNS void lookup limit during evaluation of A mechanism of m04.mailpath.io) …
Authentication-Results: ukr.net; spf=permerror (DNS void lookup limit during evaluation of A mechanism
    of m04.mailpath.io) smtp.mailfrom=m04.mailpath.io; dmarc=fail header.from=…@m04.mailpath.io
```

m10 (`ptr:mailgun.net`, spam), test 2026-10-23-06:21:38:645t:

```
Received-SPF: fail (frv72.fwdcdn.com: domain of m10.mailpath.io does not designate 159.135.228.37 as permitted sender) …
Authentication-Results: ukr.net; spf=fail (domain of m10.mailpath.io does not designate 159.135.228.37
    as permitted sender) smtp.mailfrom=m10.mailpath.io; dmarc=fail header.from=…@m10.mailpath.io
```

## m11 (two records) at Outlook.com and Hotmail

The two Microsoft consumer seeds that received the message (inbox), test 2026-10-23-06:21:37:869t;
the other four were refused at SMTP with `5.7.509` (`events.csv`).

```
Outlook  Authentication-Results: mx.microsoft.com …; spf=pass (sender IP is 159.135.228.62)
             smtp.mailfrom=m11.mailpath.io; dkim=none (message not signed) header.d=none;
             dmarc=pass … header.from=m11.mailpath.io; compauth=pass …
         Received-SPF: Pass (protection.outlook.com: domain of m11.mailpath.io designates
             159.135.228.62 as permitted sender) …
Hotmail  the same, from 159.135.228.39
```
