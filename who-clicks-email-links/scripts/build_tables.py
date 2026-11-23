#!/usr/bin/env python3
"""Build the result tables of the link-scanning test from data/messages.csv and data/requests.csv.

Writes to results/:
- copies.csv: one row per message: where it landed, whether its links were opened, by what, when,
  which link variants, whether the page scripts ran, rewritten requests, one-time links used up,
  the image, and the networks (ASN) that fetched anything.
- providers.csv: one row per run and seed provider.
- microsoft.csv: the Microsoft 365 business mailboxes (Exchange (Office365), Microsoft (EOP)) across
  the runs: format, whether the links were opened, GlockApps' delivery time.
- microsoft-variants.csv: what Microsoft's scanner did with each link variant, over the messages it
  opened.
- summary.txt: the numbers quoted in the article.

Delays of the host's requests count from Mailgun's delivered event; GlockApps' delay is its own
figure for arrival in the mailbox. Standard library only.

Usage, from the folder: python3 scripts/build_tables.py
"""
import collections
import csv
import os
import statistics

RUNS = ["l1", "l2", "l3", "l4", "l5", "l6"]
MS_BUSINESS = {"Exchange (Office365)", "Microsoft (EOP)"}
LINK_VARIANTS = ["V1", "V2", "V3", "V4", "V5", "V6", "V8", "V9", "V10", "V11", "V12", "V13", "V14", "V15"]
ONE_TIME = ["V3", "V4", "V10", "V11", "V12", "V13", "V14", "V15"]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def variants_of(fmt, run):
    """The variants a message carried: V11 from l2 on, V12 and V13 from l5 on; nolinks none; unsub
    (l6) its own five, V15 in the List-Unsubscribe header."""
    v = {"text": ["V1", "V2", "V3", "V4", "V8", "V9", "V10", "V11", "V12", "V13"],
         "html": ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13"],
         "unsub": ["V1", "V7", "V11", "V14", "V15"]}.get(fmt, [])
    since = {"V11": "l2", "V12": "l5", "V13": "l5"}
    return [x for x in v if run >= since.get(x, "l1")]


def secs(ms):
    return round(int(ms) / 1000)


def write(name, rows, fields):
    with open(os.path.join(HERE, "results", name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    msgs = list(csv.DictReader(open(os.path.join(HERE, "data", "messages.csv"))))
    reqs = list(csv.DictReader(open(os.path.join(HERE, "data", "requests.csv"))))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    by = collections.defaultdict(list)
    for x in reqs:
        if x["run"]:
            by[(x["run"], x["mailbox"])].append(x)

    copies = []
    for m in msgs:
        H = sorted(by.get((m["run"], m["mailbox"]), []), key=lambda x: int(x["ms_after_delivery"]))
        links = [x for x in H if x["variant"] in LINK_VARIANTS and x["kind"] == "page"]
        image = [x for x in H if x["variant"] == "V7"]
        notes = collections.Counter(n for x in H for n in x["note"].split())
        used = [x for x in H if "used_now" in x["note"].split()]
        copies.append(dict(m, **{
            "opened_links": "yes" if links else "no",
            "links_by": ";".join(sorted({x["fetcher"] for x in links})),
            "first_link_s": secs(links[0]["ms_after_delivery"]) if links else "",
            "last_link_s": secs(links[-1]["ms_after_delivery"]) if links else "",
            "variants_requested": ",".join(sorted({x["variant"] for x in links}, key=lambda v: int(v[1:]))),
            "ran_scripts": "yes" if notes["beacon"] else "no",
            "rewritten_requests": notes["mutation"],
            "used_up": ",".join(f'{x["variant"]}+{secs(x["ms_after_delivery"])}s' for x in used),
            "image_loaded": "yes" if image else "no",
            "image_by": ";".join(sorted({x["fetcher"] for x in image})),
            "first_image_s": secs(image[0]["ms_after_delivery"]) if image else "",
            "networks": ";".join(sorted({x["network"] for x in H})),
            "_links": links, "_burnt": {x["variant"] for x in used},
        }))
    pub = [k for k in copies[0] if not k.startswith("_")]
    write("copies.csv", copies, pub)

    rows = []
    groups = collections.defaultdict(list)
    for c in copies:
        groups[(c["run"], c["provider"])].append(c)
    for (run, prov), cs in sorted(groups.items()):
        def n(pred):
            return sum(1 for c in cs if pred(c))
        delays = [int(c["glockapps_delay_s"]) for c in cs if c["glockapps_delay_s"] != ""]
        rows.append({
            "run": run, "provider": prov, "copies": len(cs),
            "html": n(lambda c: c["format"] == "html"), "text": n(lambda c: c["format"] == "text"),
            "nolinks": n(lambda c: c["format"] == "nolinks"),
            "links_opened_html": n(lambda c: c["format"] == "html" and c["opened_links"] == "yes"),
            "links_opened_text": n(lambda c: c["format"] == "text" and c["opened_links"] == "yes"),
            "image_loaded": n(lambda c: c["image_loaded"] == "yes"),
            "inbox": n(lambda c: c["glockapps_placement"] == "inbox"),
            "spam": n(lambda c: c["glockapps_placement"] == "spam"),
            "median_delay_s": statistics.median(delays) if delays else "",
            "max_delay_s": max(delays) if delays else "",
            "fetchers": ";".join(sorted({x for c in cs for x in (c["links_by"] + ";" + c["image_by"]).split(";") if x})),
        })
    write("providers.csv", rows, list(rows[0]))

    ms = collections.defaultdict(dict)
    for c in copies:
        if c["provider"] in MS_BUSINESS:
            ms[c["mailbox"]][c["run"]] = c
    with open(os.path.join(HERE, "results", "microsoft.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["mailbox"] + [f"{r}_{k}" for r in RUNS for k in ("format", "links_opened", "delay_s")])
        for mb in sorted(ms):
            row = [mb]
            for r in RUNS:
                c = ms[mb].get(r)
                row += [c["format"], c["opened_links"], c["glockapps_delay_s"]] if c else ["", "", ""]
            w.writerow(row)

    scanned = [c for c in copies if "microsoft_scanner" in c["links_by"]]
    vrows = []
    for v in LINK_VARIANTS:
        carried = [c for c in scanned if v in variants_of(c["format"], c["run"])]
        pages = lambda c: [x for x in c["_links"] if x["variant"] == v]
        note = ""
        if v == "V8":
            q = [x for x in reqs if not x["run"] and x["note"] == "query_rewritten"]
            note = f"{len(q)} requests to /q from AS8075 with the query values rewritten (token unknown)"
        vrows.append({"variant": v, "copies_carrying": len(carried),
                      "requested": sum(1 for c in carried if pages(c)),
                      "requested_as_sent": sum(1 for c in carried if any("mutation" not in x["note"] for x in pages(c))),
                      "requested_rewritten": sum(1 for c in carried if any("mutation" in x["note"] for x in pages(c))),
                      "used_up": sum(1 for c in carried if v in c["_burnt"]) if v in ONE_TIME else "",
                      "note": note})
    write("microsoft-variants.csv", vrows, list(vrows[0]))

    ex = [c for c in copies if c["provider"] == "Exchange (Office365)" and c["glockapps_delay_s"] != ""]
    sc = [int(c["glockapps_delay_s"]) for c in ex if c["opened_links"] == "yes"]
    un = [int(c["glockapps_delay_s"]) for c in ex if c["opened_links"] == "no"]
    t = lambda k: [int(c[k]) for c in scanned if c[k] != ""]
    used = [int(u.split("+")[1][:-1]) for c in scanned for u in c["used_up"].split(",") if u]
    google = [c for c in copies if c["provider"].startswith(("Gmail", "Google")) and c["format"] in ("html", "unsub")]
    lines = [
        f"messages: {len(copies)} in {len(RUNS)} runs",
        f"messages whose links were opened: {len(scanned)}, by {dict(collections.Counter(c['links_by'] for c in copies if c['links_by']))}",
        f"Microsoft 365 business messages with links: {sum(1 for c in copies if c['provider'] in MS_BUSINESS and c['format'] != 'nolinks')}",
        f"scanner timing after delivery: image {min(t('first_image_s'))} to {max(t('first_image_s'))} s, "
        f"first link {min(t('first_link_s'))} to {max(t('first_link_s'))} s, last link {min(t('last_link_s'))} to {max(t('last_link_s'))} s, "
        f"one-time links used up {min(used)} to {max(used)} s",
        f"Exchange delivery time in GlockApps: scanned {len(sc)} messages {min(sc)} to {max(sc)} s, not scanned {len(un)} messages {min(un)} to {max(un)} s",
        f"Google image proxy: {sum(1 for c in google if 'google_image_proxy' in c['image_by'])} of {len(google)} HTML messages to Gmail and Google Workspace",
    ]
    for v in vrows:
        if v["variant"] in ONE_TIME:
            lines.append(f"{v['variant']}: carried by {v['copies_carrying']} scanned messages, requested as sent in {v['requested_as_sent']}, used up in {v['used_up']}")
    with open(os.path.join(HERE, "results", "summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
