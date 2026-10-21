"""DNS answers shared by verify.py and trace_spf.py.

Both scripts ask lookup(name, rtype) and get back (rcode, answers):

  Replay(path)  answers from a JSON fixture; a name the fixture lacks stops the run
  Live()        live answers from 1.1.1.1; save() merges them into a fixture file

Answers are TXT: list of the record's strings, A/AAAA: address,
PTR: name without the trailing dot, MX: [preference, exchange].
"""
import json
from datetime import datetime, timezone
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'dns-2026-10-21.json'
RESOLVER = '1.1.1.1'


def key(name, rtype):
    return f'{name.rstrip(".").lower()}|{rtype.upper()}'


class Replay:
    def __init__(self, path=FIXTURE):
        self.path = Path(path)
        self.answers = json.loads(self.path.read_text())['answers']

    def lookup(self, name, rtype):
        k = key(name, rtype)
        if k not in self.answers:
            raise SystemExit(f'{self.path.name} has no answer for {k}; record one with --live --save FILE')
        return self.answers[k]['rcode'], self.answers[k]['answers']


class Live:
    def __init__(self):
        import dns.resolver
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = [RESOLVER]
        self.resolver.lifetime = 10
        self.answers = {}

    def lookup(self, name, rtype):
        import dns.exception
        import dns.rcode
        import dns.resolver
        try:
            ans = self.resolver.resolve(name, rtype, raise_on_no_answer=False)
            rcode = dns.rcode.to_text(ans.response.rcode())
            answers = [_encode(rtype, r) for r in ans.rrset] if ans.rrset is not None else []
        except dns.resolver.NXDOMAIN:
            rcode, answers = 'NXDOMAIN', []
        except dns.resolver.NoNameservers:
            rcode, answers = 'SERVFAIL', []
        except dns.exception.Timeout:
            rcode, answers = 'TIMEOUT', []
        self.answers[key(name, rtype)] = {'rcode': rcode, 'answers': answers}
        return rcode, answers

    def save(self, path):
        """Merge every answer looked up so far into the fixture at path; return its size."""
        path = Path(path)
        data = json.loads(path.read_text()) if path.exists() else {
            'recorded': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 'resolver': RESOLVER, 'answers': {}}
        data['answers'] = dict(sorted({**data['answers'], **self.answers}.items()))
        path.write_text(json.dumps(data, indent=1) + '\n')
        return len(data['answers'])


def _encode(rtype, rdata):
    if rtype == 'TXT':
        return [s.decode('utf-8', 'surrogateescape') for s in rdata.strings]
    if rtype == 'MX':
        return [rdata.preference, rdata.exchange.to_text(omit_final_dot=True)]
    if rtype == 'PTR':
        return rdata.target.to_text(omit_final_dot=True)
    return rdata.address
