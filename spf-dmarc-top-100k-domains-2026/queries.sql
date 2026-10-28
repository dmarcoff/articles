-- Queries for the study. Except for the coverage query and the scan health list, they
-- read the analysed domains only: those whose scan neither timed out nor hit a
-- temporary DNS failure. `domain-scan stats -scan-id <id> -analysis` runs them all; by hand,
-- select the database (dmarkoff_dev in the cluster) and pass the scan id as a parameter
-- (clickhouse-client --param_scan_id=full-100k; the Cloud console asks for it). Every
-- statement needs the comment right above it: stats prints it as the title.
-- Every query reads the latest attempt per domain (FINAL). "Mail domains" = domains with MX
-- records and no null MX.

-- Coverage: how many domains could be checked at all.
SELECT count() AS domains,
       countIf(timed_out = 1 OR temp_failure = 1) AS not_checked,
       countIf(length(mx_hosts) > 0 AND mx_null = 0) AS mail_domains,
       countIf(spf_record != '') AS with_spf,
       countIf(dmarc_record != '') AS with_dmarc
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String};

-- The study's populations per rank bucket (ranks 1-1,000, 1,001-10,000,
-- 10,001-100,000): analysed domains, non-null MX, SPF (one record, or two and more),
-- DMARC at _dmarc (the checker reports a record found only in the domain's own TXT as
-- policy unknown) and BIMI.
SELECT multiIf(rank <= 1000, '1: top 1k', rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
       count() AS analysed,
       countIf(length(mx_hosts) > 0 AND mx_null = 0) AS with_mx,
       countIf(spf_records = 1) AS one_spf,
       countIf(spf_records >= 2) AS several_spf,
       countIf(dmarc_record != '' AND dmarc_p != 'unknown') AS with_dmarc,
       countIf(dmarc_p = 'unknown') AS dmarc_misplaced,
       countIf(bimi_record != '') AS with_bimi
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0
GROUP BY bucket ORDER BY bucket;

-- SPF and DMARC by whether the domain takes mail: a working MX, a null MX (RFC 7505)
-- or no MX at all. Most domains without MX are CDN, API and tracking hosts that send
-- no mail.
SELECT multiIf(mx_null = 1, 'null MX', length(mx_hosts) > 0, 'MX', 'no MX') AS mail,
       count() AS domains,
       countIf(spf_records > 0) AS with_spf,
       countIf(dmarc_record != '') AS with_dmarc,
       countIf(dmarc_p IN ('reject', 'quarantine')) AS enforcing,
       round(100 * with_spf / domains, 1) AS spf_pct,
       round(100 * with_dmarc / domains, 1) AS dmarc_pct
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0
GROUP BY mail ORDER BY domains DESC;

-- SPF lookups by rank bucket (domains with SPF).
SELECT multiIf(rank <= 1000, '1: top 1k', rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
       countIf(spf_record != '') AS with_spf,
       countIf(spf_lookups > 10) AS over_limit,
       round(100 * over_limit / with_spf, 2) AS over_limit_pct,
       quantile(0.5)(spf_lookups) AS median_lookups
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND spf_record != ''
GROUP BY bucket ORDER BY bucket;

-- Lookup histogram, for the chart with the line at 10.
SELECT least(spf_lookups, 20) AS lookups, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND spf_record != ''
GROUP BY lookups ORDER BY lookups;

-- Permerror by scope and by the check that failed.
SELECT spf_permerror_scope AS scope, err AS error, count() AS domains
FROM domain_scan_results FINAL ARRAY JOIN spf_errors AS err
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND spf_evaluation = 'permerror' AND err LIKE 'Critical:%'
GROUP BY scope, error ORDER BY domains DESC;

-- SPF records per domain (two or more = permerror for everyone).
SELECT spf_records AS records, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0
GROUP BY records ORDER BY records;

-- The all qualifier, ptr, void lookups.
SELECT spf_all AS all_term, count() AS domains,
       countIf(spf_has_ptr = 1) AS with_ptr,
       countIf(spf_void_lookups > 2) AS void_over_2
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND spf_record != ''
GROUP BY all_term ORDER BY domains DESC;

-- SPF records without an all term, by whether they end in a redirect: without
-- either, a sender no mechanism matches gets neutral.
SELECT if(spf_has_redirect = 1, 'redirect', 'no redirect') AS ending, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND spf_record != '' AND spf_all = ''
GROUP BY ending ORDER BY domains DESC;

-- Which includes are most common and what they cost in lookups.
SELECT inc AS include, count() AS domains, round(avg(cost), 1) AS avg_lookups, max(cost) AS max_lookups
FROM domain_scan_results FINAL ARRAY JOIN spf_includes AS inc, spf_include_lookups AS cost, spf_include_kinds AS kind
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND kind = 'include'
GROUP BY include ORDER BY domains DESC LIMIT 50;

-- DMARC policy by rank bucket.
SELECT multiIf(rank <= 1000, '1: top 1k', rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
       if(dmarc_record = '', '(none)', dmarc_p) AS policy, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0
GROUP BY bucket, policy ORDER BY bucket, domains DESC;

-- DMARC policy by rank bucket, domains with a non-null MX only.
SELECT multiIf(rank <= 1000, '1: top 1k', rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
       multiIf(dmarc_record = '', '(none)', dmarc_p = 'unknown', 'misplaced',
               dmarc_p IN ('reject', 'quarantine', 'none'), dmarc_p, 'malformed') AS policy,
       count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND length(mx_hosts) > 0 AND mx_null = 0
GROUP BY bucket, policy ORDER BY bucket, domains DESC;

-- Enforcing policies applied to part of the mail: p=reject or quarantine with the
-- legacy pct below 100.
SELECT dmarc_p AS policy, countIf(dmarc_pct < 100) AS pct_below_100, countIf(dmarc_pct = 0) AS pct_zero, count() AS enforcing
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_p IN ('reject', 'quarantine')
GROUP BY policy ORDER BY policy;

-- p=reject or quarantine with an SPF record that breaks: their mail relies on DKIM.
SELECT dmarc_p AS policy, spf_permerror_scope AS scope, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_p IN ('reject', 'quarantine') AND spf_evaluation = 'permerror'
GROUP BY policy, scope ORDER BY domains DESC;

-- pct below 100.
SELECT dmarc_pct AS pct, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_record != '' AND dmarc_pct < 100
GROUP BY pct ORDER BY domains DESC;

-- Where aggregate reports go: own organizational domain, an external one, both, or none.
SELECT multiIf(rank <= 1000, '1: top 1k', rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
       multiIf(length(dmarc_rua_orgs) = 0, 'no rua',
               has(dmarc_rua_external, 1) AND has(dmarc_rua_external, 0), 'own + external',
               has(dmarc_rua_external, 1), 'external only', 'own only') AS reports,
       count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_record != ''
GROUP BY bucket, reports ORDER BY bucket, domains DESC;

-- External report destinations by kind: a DMARC vendor, the organization's own sister
-- domain (in-house), a government collector, a personal mailbox, or not mapped yet. A
-- domain with destinations of two kinds counts for both.
SELECT if(s.kind = '', '(unmapped)', s.kind) AS destination, uniqExact(r.domain) AS domains
FROM domain_scan_results AS r FINAL
ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext
LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND ext = 1
GROUP BY destination ORDER BY domains DESC;

-- DMARC services: domains whose rua sends reports to each vendor. A domain with two
-- services counts for both. In-house, government and mailbox destinations are left
-- out; external organizations not in domain_scan_dmarc_services come out as '(unmapped)'.
SELECT if(s.service = '', '(unmapped)', s.service) AS service, uniqExact(r.domain) AS domains
FROM domain_scan_results AS r FINAL
ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext
LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND ext = 1 AND s.kind IN ('vendor', '')
GROUP BY service ORDER BY domains DESC;

-- Domains with DMARC that send reports to at least one DMARC vendor, by rank bucket.
SELECT multiIf(rank <= 1000, '1: top 1k', rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
       uniqExact(r.domain) AS with_dmarc,
       uniqExactIf(r.domain, s.kind = 'vendor') AS with_vendor,
       round(100 * with_vendor / with_dmarc, 1) AS vendor_pct
FROM domain_scan_results AS r FINAL
LEFT ARRAY JOIN r.dmarc_rua_orgs AS org
LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND r.dmarc_record != ''
GROUP BY bucket ORDER BY bucket;

-- External organizations that aren't mapped to a service yet: candidates for
-- dmarc_services.csv. The report hosts usually give the service away
-- (mxtoolbox.dmarc-report.com).
SELECT org, uniqExact(r.domain) AS domains, groupUniqArray(5)(host) AS report_hosts, any(r.domain) AS example
FROM domain_scan_results AS r FINAL
ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_domains AS host, r.dmarc_rua_external AS ext
LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND ext = 1 AND s.service = ''
GROUP BY org ORDER BY domains DESC LIMIT 100;

-- Domains with an external rua address, and how many have at least one external
-- address whose report domain doesn't authorize it (or the lookup failed).
SELECT countIf(has(dmarc_rua_external, 1)) AS with_external,
       countIf(arrayExists((e, a) -> e = 1 AND a = 0, dmarc_rua_external, dmarc_rua_authorized)) AS with_unauthorized,
       countIf(arrayExists((e, a) -> e = 1 AND a = -1, dmarc_rua_external, dmarc_rua_authorized)) AS with_lookup_failed,
       round(100 * with_unauthorized / with_external, 2) AS unauthorized_pct
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_record != '';

-- External rua without the authorization record (<domain>._report._dmarc.<report domain>),
-- by service: receivers may skip such addresses.
SELECT if(s.service = '', org, s.service) AS destination,
       uniqExact(r.domain) AS domains,
       uniqExactIf(r.domain, auth = 0) AS unauthorized,
       uniqExactIf(r.domain, auth = -1) AS lookup_failed
FROM domain_scan_results AS r FINAL
ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext, r.dmarc_rua_authorized AS auth
LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND ext = 1
GROUP BY destination HAVING unauthorized > 0 ORDER BY unauthorized DESC LIMIT 30;

-- Domains that send no mail and say so: null MX, or no MX with v=spf1 -all, and DMARC reject.
SELECT countIf(mx_null = 1) AS null_mx,
       countIf(length(mx_hosts) = 0 AND spf_record = 'v=spf1 -all') AS no_mx_spf_minus_all,
       countIf(length(mx_hosts) = 0 AND spf_record = 'v=spf1 -all' AND dmarc_p = 'reject') AS fully_parked
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0;

-- MTA-STS, TLS-RPT, BIMI, DNSSEC among mail domains.
SELECT count() AS mail_domains,
       countIf(mtasts_id != '') AS mtasts_record,
       countIf(mtasts_mode = 'enforce') AS mtasts_enforce,
       countIf(tlsrpt = 1) AS tlsrpt,
       countIf(bimi_record != '') AS bimi,
       countIf(bimi_vmc = 1) AS bimi_certificate,
       countIf(dnssec_signed = 1) AS dnssec,
       countIf(dnssec_bogus = 1) AS dnssec_bogus
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND length(mx_hosts) > 0 AND mx_null = 0;

-- MTA-STS among mail domains that publish the TXT record: whether the policy loads,
-- and its mode.
SELECT multiIf(mtasts_policy_found = 0, 'record, policy not loaded', mtasts_mode = '', 'policy without a mode', mtasts_mode) AS mtasts,
       count() AS domains,
       countIf(tlsrpt = 1) AS with_tlsrpt
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND length(mx_hosts) > 0 AND mx_null = 0 AND mtasts_id != ''
GROUP BY mtasts ORDER BY domains DESC;

-- BIMI records (default selector) with a certificate URL (a=), and how many of those
-- certificates were read; the rest failed to download or parse.
SELECT count() AS bimi_records,
       countIf(match(bimi_record, '(?i)(^|;)\\s*a\\s*=\\s*[^;\\s]')) AS with_certificate_url,
       countIf(bimi_vmc = 1) AS certificate_read
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND bimi_record != '';

-- BIMI mark certificates by type and by whether they had expired on the scan day.
SELECT if(cert_type = '', '(type unread)', cert_type) AS certificate,
       multiIf(not_after IS NULL, 'expiry unread', not_after < scanned_at, 'expired',
               not_after < scanned_at + INTERVAL 30 DAY, 'expires within 30 days', 'valid') AS state,
       count() AS domains
FROM (
    SELECT scanned_at,
           JSONExtractString(raw, 'bimi', 'vmc', 'certType') AS cert_type,
           parseDateTimeBestEffortOrNull(substring(JSONExtractString(raw, 'bimi', 'vmc', 'notAfter'), 1, 19), 'UTC') AS not_after
    FROM domain_scan_results FINAL
    WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND bimi_vmc = 1
)
GROUP BY certificate, state ORDER BY certificate, domains DESC;

-- BIMI records: the checks that fail most often.
SELECT err AS error, count() AS domains
FROM domain_scan_results FINAL ARRAY JOIN bimi_errors AS err
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND bimi_record != ''
GROUP BY error ORDER BY domains DESC LIMIT 15;

-- BIMI records by the domain's DMARC: mailbox providers show a logo only under an
-- enforcing policy applied to all mail.
SELECT multiIf(dmarc_record = '', 'no DMARC record',
               dmarc_p NOT IN ('reject', 'quarantine', 'none'), 'malformed p=',
               dmarc_p = 'none', 'p=none',
               dmarc_pct < 100, 'enforcing, pct below 100', 'enforcing') AS dmarc,
       count() AS domains,
       countIf(bimi_vmc = 1) AS with_certificate
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND bimi_record != ''
GROUP BY dmarc ORDER BY domains DESC;

-- p= values receivers don't recognise, as written (lowercased); a missing or empty tag
-- has its own row.
SELECT multiIf(NOT match(dmarc_record, '(?i)(^|;)\\s*p\\s*='), '(no p= tag)',
               raw_p = '', '(empty p=)', raw_p) AS p_value,
       count() AS domains
FROM (
    SELECT dmarc_record, lower(trimBoth(extract(dmarc_record, '(?i)(?:^|;)\\s*p\\s*=\\s*([^;]*)'))) AS raw_p
    FROM domain_scan_results FINAL
    WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_record != '' AND dmarc_p NOT IN ('none', 'quarantine', 'reject')
)
GROUP BY p_value ORDER BY domains DESC LIMIT 30;

-- DMARC records: the checks that fail most often.
SELECT err AS error, count() AS domains
FROM domain_scan_results FINAL ARRAY JOIN dmarc_errors AS err
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_record != ''
GROUP BY error ORDER BY domains DESC LIMIT 20;

-- DMARC policy of the domains that ask for no aggregate reports, next to those that
-- do: without rua nobody hears about failing mail.
SELECT if(length(dmarc_rua) = 0, 'no rua', 'with rua') AS reports,
       if(dmarc_p IN ('reject', 'quarantine', 'none'), dmarc_p, 'malformed') AS policy,
       count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_record != ''
GROUP BY reports, policy ORDER BY reports, domains DESC;

-- Enforcing domains by their subdomain policy: sp=none leaves subdomains open.
SELECT dmarc_p AS policy, if(dmarc_sp = '', '(not set)', dmarc_sp) AS subdomain_policy, count() AS domains
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND dmarc_p IN ('reject', 'quarantine')
GROUP BY policy, subdomain_policy ORDER BY policy, domains DESC;

-- SPF health by where the domain's DMARC reports go: no DMARC, no rua, own domain
-- only, or each kind of external destination. A domain that reports to two kinds
-- counts for both.
SELECT destination,
       uniqExact(domain) AS domains,
       uniqExactIf(domain, spf_records > 0) AS with_spf,
       uniqExactIf(domain, spf_evaluation = 'permerror') AS spf_permerror,
       uniqExactIf(domain, spf_records = 0) AS no_spf,
       round(100 * spf_permerror / with_spf, 2) AS permerror_pct_of_spf
FROM (
    SELECT r.domain AS domain, r.spf_evaluation AS spf_evaluation, r.spf_records AS spf_records,
           multiIf(r.dmarc_record = '', 'no DMARC',
                   length(r.dmarc_rua_orgs) = 0, 'no rua',
                   NOT has(r.dmarc_rua_external, 1), 'own domain only',
                   ext = 0, '',
                   s.kind = '', '(unmapped)', s.kind) AS destination
    FROM domain_scan_results AS r FINAL
    LEFT ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext
    LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
    WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0
)
WHERE destination != ''
GROUP BY destination ORDER BY domains DESC;

-- SPF permerror among the domains of each DMARC vendor with 100 domains or more:
-- does reporting to a vendor go with a working SPF?
SELECT s.service AS service,
       uniqExact(r.domain) AS domains,
       uniqExactIf(r.domain, r.spf_evaluation = 'permerror') AS spf_permerror,
       uniqExactIf(r.domain, r.spf_record != '' AND r.spf_lookups > 10) AS over_limit,
       round(100 * spf_permerror / domains, 2) AS permerror_pct
FROM domain_scan_results AS r FINAL
ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext
INNER JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND ext = 1 AND s.kind = 'vendor'
GROUP BY service HAVING domains >= 100 ORDER BY permerror_pct DESC;

-- The same SPF permerror share among domains with SPF, by report destination and rank
-- bucket, to see whether rank explains the difference between destinations.
SELECT destination, bucket,
       uniqExactIf(domain, spf_records > 0) AS with_spf,
       uniqExactIf(domain, spf_evaluation = 'permerror') AS spf_permerror,
       round(100 * spf_permerror / with_spf, 2) AS permerror_pct_of_spf
FROM (
    SELECT r.domain AS domain, r.spf_evaluation AS spf_evaluation, r.spf_records AS spf_records,
           multiIf(r.rank <= 1000, '1: top 1k', r.rank <= 10000, '2: 1k-10k', '3: 10k-100k') AS bucket,
           multiIf(r.dmarc_record = '', 'no DMARC',
                   length(r.dmarc_rua_orgs) = 0, 'no rua',
                   NOT has(r.dmarc_rua_external, 1), 'own domain only',
                   ext = 0, '',
                   s.kind = 'vendor', 'vendor', '') AS destination
    FROM domain_scan_results AS r FINAL
    LEFT ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext
    LEFT JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
    WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0
)
WHERE destination != ''
GROUP BY destination, bucket ORDER BY destination, bucket;

-- Domains that send aggregate reports to more than one DMARC vendor, often left over
-- from a switch.
SELECT vendors, count() AS domains
FROM (
    SELECT r.domain AS domain, uniqExact(s.service) AS vendors
    FROM domain_scan_results AS r FINAL
    ARRAY JOIN r.dmarc_rua_orgs AS org, r.dmarc_rua_external AS ext
    INNER JOIN domain_scan_dmarc_services AS s ON s.org_domain = org
    WHERE r.scan_id = {scan_id:String} AND r.timed_out = 0 AND r.temp_failure = 0 AND ext = 1 AND s.kind = 'vendor'
    GROUP BY domain
)
GROUP BY vendors ORDER BY vendors;

-- SPF includes and redirects that point at names that don't exist (NXDOMAIN), by what
-- the registrable domain behind each name is (the includes command fills
-- domain_scan_include_targets; unregistered means it doesn't resolve, so confirm with
-- WHOIS: many are registered but held or without name servers). Whoever registers an unregistered one can make mail
-- from their servers pass SPF for every domain that includes it. Publish counts only.
WITH missing AS (
    SELECT domain,
           arrayDistinct(arrayMap(t -> lower(t), arrayFilter(t -> position(t, '%') = 0,
               extractAll(raw, 'does not exist \\(NXDOMAIN\\)[^"]*","value":"([^"]+)"')))) AS names
    FROM domain_scan_results FINAL
    WHERE scan_id = {scan_id:String} AND timed_out = 0 AND temp_failure = 0 AND position(raw, 'NXDOMAIN') > 0
)
SELECT if(i.status = '', '(not classified)', i.status) AS registrable_domain,
       uniqExact(domain) AS domains,
       uniqExact(name) AS targets
FROM missing ARRAY JOIN names AS name
LEFT JOIN (SELECT target, status FROM domain_scan_include_targets FINAL WHERE scan_id = {scan_id:String}) AS i ON i.target = name
GROUP BY registrable_domain ORDER BY domains DESC;

-- Scan health: the slowest domains and the checker errors.
SELECT domain, rank, duration_ms, timed_out, checker_errors
FROM domain_scan_results FINAL
WHERE scan_id = {scan_id:String}
ORDER BY duration_ms DESC LIMIT 20;
