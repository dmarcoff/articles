# Bounce server (direct path)

Every direct-path case domain (`s00` to `s12.mailpath.io`) had `MX 10 mta.mailpath.io`, our sending
host (see each run's `dns.json`), and every message went out with a VERP sender address on its case
domain. A delivery status notification (DSN) for any message would have come back to that host,
where `bouncesrv` ran from 2026-10-21 19:21 UTC, before the pilot, until we read its log on
2026-10-25, without a restart.

It received four messages in that time, all of them our own: three Mailgun probes sent to
`postmaster@s01.mailpath.io` on 2026-10-22 while we set up the Mailgun path, and one delivery test
from `m01.mailpath.io` on 2026-10-23. No receiver sent a DSN for any of the 3,202 direct-path
messages, 1,033 of which were accepted, including the ones that were accepted and never reached a
mailbox (Seznam's and Microsoft's).

The raw log stays in our private working repository; it holds nothing beyond those four messages.
