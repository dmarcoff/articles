#!/usr/bin/env python3
"""Step-by-step RFC 7208 check_host() trace, to read along with the article.

A tracing aid, not a full SPF implementation: verify.py checks the same
scenarios with pySPF. DNS answers come from the same fixture, or from
1.1.1.1 with --live.

  python trace_spf.py eval <ip> <domain> [--record R] [--sender S]
      one check: every DNS-querying term, void lookup and match; --record
      evaluates R instead of the domain's TXT (includes still resolve)
  python trace_spf.py static <domain> [--record R]
      every DNS-querying term in the record tree, in order, whether or not an
      evaluation reaches it, plus the RFC 7208 section 3.4 size measure
  python trace_spf.py all
      eval for every scenario in scenarios.json, then static for each domain
  python trace_spf.py dump <domain>...
      raw TXT answers along every SPF chain via dig, live only; this is how
      data/dns-snapshot-*.txt were captured

Rules it applies (RFC 7208):
  - the whole record is syntax-checked first (4.6): an unknown mechanism or a
    malformed ip4/ip6 anywhere is a permerror, even after a matching term;
  - unknown modifiers are ignored, but their value must be a valid macro-string
    (6, 7.1); a second redirect= or exp= is a permerror;
  - the 11th DNS-querying term is a permerror and isn't queried (4.6.4);
  - the 3rd void lookup is a permerror (4.6.4); an include/redirect target with
    no TXT records counts as one, as pySPF counts it;
  - an include target without an SPF record is a permerror (5.2);
  - a/mx look up A for an IPv4 sender and AAAA for IPv6 (5.3, 5.4);
  - a DNS error other than NXDOMAIN is a temperror; on ptr lookups it just
    doesn't match (5, 5.5).
"""
import argparse
import ipaddress
import json
import re
import subprocess
import sys
from pathlib import Path

import spfdns

HERE = Path(__file__).resolve().parent
DNS = None  # spfdns.Replay or spfdns.Live, set in main()
_cache = {}
MECHANISMS = ('all', 'include', 'a', 'mx', 'ptr', 'ip4', 'ip6', 'exists')


# ---------------------------------------------------------------- DNS
def query(name, rtype):
    """Return (rcode, answers). TXT answers are the record's strings joined."""
    k = spfdns.key(name, rtype)
    if k not in _cache:
        rcode, answers = DNS.lookup(name, rtype)
        if rtype == 'TXT':
            answers = [''.join(a) for a in answers]
        _cache[k] = (rcode, answers)
    return _cache[k]


def txt_chunks(rdata):
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', rdata)
    out = []
    for s in strings:
        b = bytearray()
        i = 0
        while i < len(s):
            if s[i] == '\\' and s[i + 1:i + 4].isdigit() and len(s[i + 1:i + 4]) == 3:
                b.append(int(s[i + 1:i + 4])); i += 4
            elif s[i] == '\\' and i + 1 < len(s):
                b += s[i + 1].encode(); i += 2
            else:
                b += s[i].encode(); i += 1
        out.append(bytes(b))
    return out


def is_spf(v):
    return v.lower() == 'v=spf1' or v.lower().startswith('v=spf1 ')


# ---------------------------------------------------------------- syntax (RFC 7208 §12, simplified)
class PermError(Exception):
    pass


class TempError(Exception):
    pass


MACRO_RE = re.compile(r'%\{[slodiphcrtvSLODIPHCRTV]\d*r?[.\-+,/_=]*\}|%%|%_|%-')


def valid_macro_string(s):
    rest = MACRO_RE.sub('', s)
    return '%' not in rest and all(0x21 <= ord(c) <= 0x7e for c in rest)


def valid_domain_spec(s):
    return bool(s) and valid_macro_string(s)


def parse_record(record):
    """Return list of ('mech', qualifier, name, arg) / ('mod', name, value); raise PermError."""
    terms = [t for t in record.split(' ') if t][1:]
    parsed, seen_mods = [], set()
    for t in terms:
        m = re.match(r'^([+\-~?]?)([A-Za-z][A-Za-z0-9]*)(.*)$', t)
        name = m.group(2).lower() if m else ''
        rest = m.group(3) if m else ''
        if m and name in MECHANISMS and (rest == '' or rest[0] in ':/'):
            q = m.group(1) or '+'
            if name == 'all':
                if rest:
                    raise PermError(f'syntax error in "{t}": all takes no argument')
            elif name in ('include', 'exists'):
                if not rest.startswith(':') or not valid_domain_spec(rest[1:]):
                    raise PermError(f'syntax error in "{t}": {name} needs a domain')
            elif name in ('a', 'mx'):
                dm = re.match(r'^(?::([^/]+))?(?:/(\d+))?(?://(\d+))?$', rest)
                if not dm or (dm.group(1) and not valid_domain_spec(dm.group(1))):
                    raise PermError(f'syntax error in "{t}"')
                if (dm.group(2) and int(dm.group(2)) > 32) or (dm.group(3) and int(dm.group(3)) > 128):
                    raise PermError(f'syntax error in "{t}": bad CIDR length')
            elif name == 'ptr':
                if rest and (not rest.startswith(':') or not valid_domain_spec(rest[1:])):
                    raise PermError(f'syntax error in "{t}"')
            elif name in ('ip4', 'ip6'):
                if not rest.startswith(':'):
                    raise PermError(f'syntax error in "{t}"')
                addr, _, plen = rest[1:].partition('/')
                try:
                    ipo = ipaddress.ip_address(addr)
                except ValueError:
                    raise PermError(f'syntax error in "{t}": "{addr}" is not a valid address')
                if (name == 'ip4') != (ipo.version == 4):
                    raise PermError(f'syntax error in "{t}": wrong address family')
                if plen and (not plen.isdigit() or int(plen) > (32 if name == 'ip4' else 128)):
                    raise PermError(f'syntax error in "{t}": bad CIDR length')
            parsed.append(('mech', q, name, rest))
            continue
        mm = re.match(r'^([A-Za-z][A-Za-z0-9\-_.]*)=(.*)$', t)
        if mm:
            mname, value = mm.group(1).lower(), mm.group(2)
            if mname in ('redirect', 'exp'):
                if mname in seen_mods:
                    raise PermError(f'syntax error: second {mname}= modifier')
                seen_mods.add(mname)
                if not valid_domain_spec(value):
                    raise PermError(f'syntax error in "{t}"')
            elif not valid_macro_string(value):
                raise PermError(f'syntax error in "{t}": bad macro string')
            parsed.append(('mod', mname, value))
            continue
        raise PermError(f'syntax error: unknown mechanism "{t}"')
    return parsed


# ---------------------------------------------------------------- macros (§7)
def expand(spec, ip, domain, sender):
    local, _, sdom = sender.rpartition('@') if '@' in sender else ('postmaster', '', sender)
    ipobj = ipaddress.ip_address(ip)
    idot = str(ipobj) if ipobj.version == 4 else '.'.join(ipobj.exploded.replace(':', ''))
    vals = {'s': sender, 'l': local or 'postmaster', 'o': sdom, 'd': domain, 'i': idot, 'p': 'unknown',
            'h': domain, 'v': 'in-addr' if ipobj.version == 4 else 'ip6', 'c': ip, 'r': 'unknown', 't': '0'}

    def rep(m):
        letter, digits, rev, delims = m.group(1), m.group(2), m.group(3), m.group(4)
        val = vals[letter.lower()]
        if digits or rev or delims:
            parts = re.split('[' + re.escape(delims or '.') + ']', val)
            if rev:
                parts = parts[::-1]
            if digits:
                parts = parts[-int(digits):]
            val = '.'.join(parts)
        return val
    s = re.sub(r'%\{([slodiphcrtvSLODIPHCRTV])(\d*)(r?)([.\-+,/_=]*)\}', rep, spec)
    return s.replace('%%', '%').replace('%_', ' ').replace('%-', '%20')


# ---------------------------------------------------------------- evaluator
class State:
    def __init__(self):
        self.lookups = 0
        self.voids = 0
        self.trace = []

    def log(self, depth, msg):
        self.trace.append('  ' * depth + msg)

    def count(self, depth, term):
        self.lookups += 1
        self.log(depth, f'[term {self.lookups}] {term}')
        if self.lookups > 10:
            raise PermError(f'DNS-querying term #{self.lookups} "{term}" exceeds the limit of 10 (not queried)')

    def void(self, depth, why):
        self.voids += 1
        self.log(depth, f'  void lookup #{self.voids} ({why})')
        if self.voids > 2:
            raise PermError(f'void lookup limit: {self.voids} void lookups (recommended limit 2)')


def addr_lookup(name, version, *, strict=True):
    rtype = 'A' if version == 4 else 'AAAA'
    rcode, ans = query(name, rtype)
    if rcode not in ('NOERROR', 'NXDOMAIN'):
        if strict:
            raise TempError(f'{rtype} {name}: {rcode}')
        return rcode, []
    return rcode, ans


def in_net(ip, addr, c4, c6):
    ipo = ipaddress.ip_address(ip)
    try:
        ao = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if ipo.version != ao.version:
        return False
    plen = int(c4 or 32) if ipo.version == 4 else int(c6 or 128)
    return ipo in ipaddress.ip_network(f'{addr}/{plen}', strict=False)


def check_host(ip, domain, sender, st, depth=0, record=None, is_target=False):
    if record is None:
        rcode, txts = query(domain, 'TXT')
        if rcode not in ('NOERROR', 'NXDOMAIN'):
            raise TempError(f'TXT {domain}: {rcode}')
        if is_target and not txts:
            st.void(depth, f'{rcode}, no TXT records at {domain}')
        spf = [t for t in txts if is_spf(t)]
        if not spf:
            st.log(depth, f'{domain}: no SPF record ({rcode}, {len(txts)} TXT)')
            return 'none'
        if len(spf) > 1:
            raise PermError(f'{domain}: {len(spf)} SPF records')
        record = spf[0]
    st.log(depth, f'{domain}: "{record}"')
    terms = parse_record(record)
    ipo = ipaddress.ip_address(ip)
    has_all = any(t[0] == 'mech' and t[2] == 'all' for t in terms)
    redirect = next((t[2] for t in terms if t[0] == 'mod' and t[1] == 'redirect'), None)
    for t in terms:
        if t[0] == 'mod':
            if t[1] not in ('redirect', 'exp'):
                st.log(depth, f'  {t[1]}={t[2]}: unknown modifier, ignored')
            continue
        _, q, mech, rest = t
        text = f'{"" if q == "+" else q}{mech}{rest}'
        result = {'+': 'pass', '-': 'fail', '~': 'softfail', '?': 'neutral'}[q]
        matched = False
        if mech == 'all':
            matched = True
        elif mech in ('ip4', 'ip6'):
            addr, _, plen = rest[1:].partition('/')
            matched = in_net(ip, addr, plen if mech == 'ip4' else None, plen if mech == 'ip6' else None)
        elif mech == 'include':
            st.count(depth, text)
            r = check_host(ip, expand(rest[1:], ip, domain, sender), sender, st, depth + 1, is_target=True)
            if r == 'none':
                raise PermError(f'include target {rest[1:]} has no SPF record (RFC 7208 §5.2)')
            if r in ('permerror', 'temperror'):
                return r
            matched = r == 'pass'
        elif mech == 'exists':
            st.count(depth, text)
            target = expand(rest[1:], ip, domain, sender)
            rcode, ans = query(target, 'A')
            if rcode not in ('NOERROR', 'NXDOMAIN'):
                raise TempError(f'A {target}: {rcode}')
            st.log(depth, f'  exists -> {target} A: {rcode} {ans}')
            if not ans:
                st.void(depth, f'{rcode} for {target}')
            matched = bool(ans)
        elif mech == 'a':
            st.count(depth, text)
            dm = re.match(r'^(?::([^/]+))?(?:/(\d+))?(?://(\d+))?$', rest)
            target = expand(dm.group(1), ip, domain, sender) if dm.group(1) else domain
            rcode, ans = addr_lookup(target, ipo.version)
            if not ans:
                st.void(depth, f'{rcode}, no {"A" if ipo.version == 4 else "AAAA"} for {target}')
            matched = any(in_net(ip, x, dm.group(2), dm.group(3)) for x in ans)
        elif mech == 'mx':
            st.count(depth, text)
            dm = re.match(r'^(?::([^/]+))?(?:/(\d+))?(?://(\d+))?$', rest)
            target = expand(dm.group(1), ip, domain, sender) if dm.group(1) else domain
            rcode, mxs = query(target, 'MX')
            if rcode not in ('NOERROR', 'NXDOMAIN'):
                raise TempError(f'MX {target}: {rcode}')
            if not mxs:
                st.void(depth, f'{rcode}, no MX for {target}')
            if len(mxs) > 10:
                raise PermError(f'mx {target}: more than 10 MX records')
            for _, exchange in mxs:
                _, ans = addr_lookup(exchange, ipo.version)
                if any(in_net(ip, x, dm.group(2), dm.group(3)) for x in ans):
                    matched = True
        elif mech == 'ptr':
            st.count(depth, text)
            target = (expand(rest[1:], ip, domain, sender) if rest else domain).lower().rstrip('.')
            rev = ipo.reverse_pointer
            rcode, names = query(rev, 'PTR')
            st.log(depth, f'  ptr -> {rev}: {rcode} {names}')
            if rcode in ('NOERROR', 'NXDOMAIN') and not names:
                st.void(depth, f'{rcode} for {rev}')
            for n in names[:10]:
                n = n.rstrip('.').lower()
                _, ans = addr_lookup(n, ipo.version, strict=False)
                if ip in ans and (n == target or n.endswith('.' + target)):
                    matched = True
        if matched:
            st.log(depth, f'  MATCH {text} -> {result}')
            return result
    if redirect and not has_all:
        st.count(depth, 'redirect=' + redirect)
        r = check_host(ip, expand(redirect, ip, domain, sender), sender, st, depth + 1, is_target=True)
        if r == 'none':
            raise PermError(f'redirect target {redirect} has no SPF record')
        return r
    return 'neutral'


def evaluate(ip, domain, sender=None, record=None):
    st = State()
    sender = sender or f'postmaster@{domain}'
    try:
        res = check_host(ip, domain, sender, st, record=record)
    except PermError as e:
        st.log(0, f'PERMERROR: {e}')
        res = 'permerror'
    except TempError as e:
        st.log(0, f'TEMPERROR: {e}')
        res = 'temperror'
    return res, st


def result_line(res, st):
    return f'RESULT: {res} | DNS-querying terms reached {st.lookups} | void lookups {st.voids}'


# ---------------------------------------------------------------- static walk and TXT dump
def static(domain, record=None, depth=0, out=None, counter=None):
    out = out if out is not None else []
    counter = counter if counter is not None else [0]
    if record is None:
        _, txts = query(domain, 'TXT')
        if depth == 0:
            size = len(domain) + sum(len(t.encode('utf-8', 'surrogateescape')) for t in txts)
            out.append(f'{domain}: {len(txts)} TXT record(s); domain name + TXT text = {size:,} bytes '
                       f'(RFC 7208 §3.4 recommends under 450)')
        recs = [t for t in txts if is_spf(t)]
        if not recs:
            out.append('  ' * depth + f'{domain}: NO SPF RECORD')
            return out
        record = recs[0]
    out.append('  ' * depth + f'{domain}: {record}')
    for t in record.split()[1:]:
        low = t.lower().lstrip('+-~?')
        if re.match(r'^(include|a|mx|ptr|exists)(:|/|$)', low) or low.startswith('redirect='):
            counter[0] += 1
            out.append('  ' * (depth + 1) + f'#{counter[0]:>2} {t}' + ('   <-- 11th term: limit exceeded here' if counter[0] == 11 else ''))
            if low.startswith('include:') or low.startswith('redirect='):
                static(re.split('[:=]', t, maxsplit=1)[1], None, depth + 2, out, counter)
    return out


def dump(domain, seen):
    if domain.lower() in seen:
        return
    seen.add(domain.lower())
    raw = subprocess.run(['dig', f'@{spfdns.RESOLVER}', domain, 'TXT', '+bufsize=1232'], capture_output=True, text=True).stdout
    size = re.search(r'MSG SIZE\s+rcvd: (\d+)', raw)
    status = re.search(r'status: (\w+)', raw)
    recs = []
    for line in raw.splitlines():
        parts = line.split(None, 4)
        if line and not line.startswith(';') and len(parts) == 5 and parts[3] == 'TXT':
            ch = txt_chunks(parts[4])
            recs.append((parts[4], [len(c) for c in ch], b''.join(ch).decode('utf-8', 'replace')))
    spf = [r for r in recs if is_spf(r[2])]
    print(f'### {domain}  (TXT status {status.group(1) if status else "?"}, {len(recs)} TXT record(s), {len(spf)} SPF, response {size.group(1) if size else "?"} bytes)')
    for pres, lens, val in recs:
        print(f'{"SPF " if is_spf(val) else "    "}{pres}   [strings: {lens}, total {sum(lens)} bytes]')
    for _, _, val in spf:
        for t in val.split()[1:]:
            low = t.lower().lstrip('+-~?')
            if low.startswith('include:') or low.startswith('redirect='):
                dump(re.split('[:=]', t, maxsplit=1)[1], seen)
    print()


def run_all():
    scenarios = json.loads((HERE / 'scenarios.json').read_text())
    agree = 0
    for sc in scenarios:
        print(f'######## {sc["ip"]} -> {sc["domain"]}' + (f' (candidate record: {sc["record"]})' if sc.get('record') else ''))
        res, st = evaluate(sc['ip'], sc['domain'], record=sc.get('record'))
        exp = sc['expect']
        ok = res == exp['result'] and st.voids == exp['void']
        agree += ok
        print('\n'.join(st.trace))
        print(result_line(res, st) + f' | expected {exp["result"]}, {exp["void"]} void: {"ok" if ok else "DIFF"}\n')
    for domain in dict.fromkeys(sc['domain'] for sc in scenarios):
        print(f'######## static {domain}')
        print('\n'.join(static(domain)) + '\n')
    print(f'{agree}/{len(scenarios)} traces agree with scenarios.json')


def main():
    global DNS
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--live', action='store_true', help='query live DNS through 1.1.1.1 instead of the fixture')
    common.add_argument('--save', metavar='FILE', help='with --live: merge every DNS answer into FILE')
    common.add_argument('--fixture', default=spfdns.FIXTURE, help='fixture file for offline mode')
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('eval', parents=[common], help='trace one check')
    p.add_argument('ip')
    p.add_argument('domain')
    p.add_argument('--record', help="evaluate this record instead of the domain's TXT")
    p.add_argument('--sender', help='MAIL FROM (default postmaster@<domain>)')
    p = sub.add_parser('static', parents=[common], help='every DNS-querying term in the record tree')
    p.add_argument('domain')
    p.add_argument('--record', help="walk this record instead of the domain's TXT")
    sub.add_parser('all', parents=[common], help='eval every scenario in scenarios.json, then static for each domain')
    p = sub.add_parser('dump', help='raw TXT along every SPF chain via dig (live only)')
    p.add_argument('domains', nargs='+')
    args = ap.parse_args()
    if args.cmd == 'dump':
        for d in args.domains:
            print(f'======== {d}')
            dump(d, set())
        return
    if args.save and not args.live:
        ap.error('--save needs --live')
    DNS = spfdns.Live() if args.live else spfdns.Replay(args.fixture)
    if args.cmd == 'eval':
        res, st = evaluate(args.ip, args.domain, args.sender, args.record)
        print('\n'.join(st.trace))
        print(result_line(res, st))
    elif args.cmd == 'static':
        print('\n'.join(static(args.domain, args.record)))
    else:
        run_all()
    if args.save:
        print(f'{args.save} now holds {DNS.save(args.save)} DNS answers', file=sys.stderr)


if __name__ == '__main__':
    main()
