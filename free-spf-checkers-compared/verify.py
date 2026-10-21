#!/usr/bin/env python3
"""Reproduce the article's reference results with pySPF.

Each scenario in scenarios.json is one SPF check: a sending IP, a domain and,
optionally, a candidate record evaluated instead of the published one.
MAIL FROM is postmaster@<domain> and HELO is <domain>.

  python verify.py                       offline: DNS answers from the fixture
  python verify.py --live                live DNS through 1.1.1.1
  python verify.py --live --save FILE    live DNS, saving every answer into FILE

Offline mode answers DNS only from the fixture and stops if pySPF asks for a
name the fixture doesn't have, so a run either reproduces the recorded DNS
state exactly or fails loudly. Live results can differ once a domain changes
its records. The exit code is 1 if any result or void count differs from the
expected one.
"""
import argparse
import json
import sys
from pathlib import Path

import spf  # pyspf

import spfdns

HERE = Path(__file__).resolve().parent


def use_dns(source):
    """Route pySPF's DNS queries through source, so both scripts see the same answers."""
    def lookup(name, qtype, tcpfallback=True, timeout=30):
        rcode, answers = source.lookup(name, qtype)
        if rcode not in ('NOERROR', 'NXDOMAIN'):
            raise spf.TempError(f'DNS {rcode} for {name} {qtype}')
        if qtype == 'TXT':
            answers = [tuple(s.encode('utf-8', 'surrogateescape') for s in a) for a in answers]
        elif qtype == 'MX':
            answers = [tuple(a) for a in answers]
        return [((name, qtype), a) for a in answers]
    spf.DNSLookup = lookup


def run(scenarios):
    failures = 0
    print(f'{"sender IP":<15} {"domain":<14} {"result":<10} {"lookups":>7} {"void":>4}  check  explanation')
    for sc in scenarios:
        domain = sc['domain']
        q = spf.query(i=sc['ip'], s=f'postmaster@{domain}', h=domain, strict=True)
        result, _, explanation = q.check(spf=sc.get('record'))
        exp = sc['expect']
        ok = result == exp['result'] and q.void_lookups == exp['void']
        failures += not ok
        label = domain + (' *' if sc.get('record') else '')
        print(f'{sc["ip"]:<15} {label:<14} {result:<10} {q.lookups:>7} {q.void_lookups:>4}  {"ok" if ok else "DIFF":<5}  {explanation}')
        if not ok:
            print(f'{"":<15} expected {exp["result"]}, {exp["void"]} void lookup(s)')
    print('* candidate record evaluated instead of the published one')
    print(f'\n{len(scenarios) - failures}/{len(scenarios)} scenarios match the expected results')
    return failures


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--live', action='store_true', help='query live DNS through 1.1.1.1 instead of the fixture')
    ap.add_argument('--save', metavar='FILE', help='with --live: merge every DNS answer into FILE')
    ap.add_argument('--fixture', default=spfdns.FIXTURE, help='fixture file for offline mode')
    args = ap.parse_args()
    if args.save and not args.live:
        ap.error('--save needs --live')
    source = spfdns.Live() if args.live else spfdns.Replay(args.fixture)
    use_dns(source)
    print(f'pyspf {spf.__version__}, ' + ('live DNS via 1.1.1.1' if args.live else f'DNS from {Path(args.fixture).name}') + '\n')
    failures = run(json.loads((HERE / 'scenarios.json').read_text()))
    if args.save:
        print(f'{args.save} now holds {source.save(args.save)} DNS answers', file=sys.stderr)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
