# Seed headers (p1)

Checked on 2026-10-25 in the Header view of GlockApps' web report (project 6), test
2026-10-21-19:27:41:736t (s02, 11 DNS lookups before `ip4`). Libero and both Virgilio seeds
(spam) write only `Received-SPF: permerror`, with no Authentication-Results; Proton (spam) writes
`spf=fail` and `dmarc=fail` in separate Authentication-Results headers. GlockApps' SPF column says
`pass` for all of them. The r2 file has the full excerpts for the same record.
