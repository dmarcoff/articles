# DMARKOFF articles

Data and scripts behind articles on the [DMARKOFF blog](https://dmarkoff.com/blog), published so readers can check the results themselves. Each folder belongs to one article and has its own README.

| Folder | Article |
|---|---|
| [free-spf-checkers-compared](free-spf-checkers-compared/) | Free SPF Checkers Compared: What They Get Wrong About Five Real-World SPF Records (October 2026) |
| [broken-spf-records-mailbox-providers](broken-spf-records-mailbox-providers/) | What Mailbox Providers Really Do With Broken SPF Records: We Tested 21 of Them (October 2026) |
| [spf-dmarc-top-100k-domains-2026](spf-dmarc-top-100k-domains-2026/) | SPF and DMARC in the Tranco Top 100,000: Our October 2026 DNS Snapshot (October 2026) |

## How to cite

[CITATION.cff](CITATION.cff) holds the citation for the whole repository; GitHub shows it as "Cite this repository". Each folder's README gives citations for its folder and for its article once the article is published. Links to `tree/main` follow later changes; to cite the files exactly as you used them, replace `main` with the commit hash.

## License

The code, meaning the `*.py` and `*.sql` files, is under the [MIT License](LICENSE). Everything else in the repository, data and documentation, is under the [Creative Commons Attribution 4.0 International License](LICENSE-DATA) (CC BY 4.0), © 2026 Aliaksandr Markau, with two exceptions.

**Screenshots.** The images in the `screenshots/` folders show the web interfaces of other vendors' SPF checkers, GlockApps, Mailgun and DMARKOFF. The interfaces belong to their owners. The screenshots are included to illustrate the articles and to let readers check them, and they are not covered by CC BY 4.0.

**Content produced by other systems.** Parts of the data were produced by systems we don't operate: DNS records of other domains, SMTP replies, Mailgun's exports, the receivers' DMARC aggregate reports, message headers and GlockApps' results. We claim no rights in that content, and CC BY 4.0 applies only within the rights we hold.

When you reuse the data, name the authors and the folder and state the license, for example:

> Data: Aliaksandr Markau and DMARKOFF, "SPF and DMARC in the Tranco top 100,000: data", https://github.com/dmarcoff/articles/tree/main/spf-dmarc-top-100k-domains-2026, CC BY 4.0.

If you changed the data, say so.
