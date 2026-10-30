# Adding data for an article

This repository holds the data and scripts behind studies published on the DMARKOFF blog, one folder per article. Other sites link to individual files here and the releases are archived on Zenodo with a DOI, so files are added, not reworked. This page describes how a new folder gets in and how a release is made.

## Where a new dataset goes

A new study goes into a new folder in this repository, whatever its topic. The repository is defined by the blog, not by SPF or DMARC; when the topic is new, update the `abstract` and `keywords` in `CITATION.cff` so the Zenodo record describes it.

Use a separate repository with its own Zenodo record instead when one of these applies:

- **Other authors.** The copyright holder here is Aliaksandr Markau, and `CITATION.cff` lists the authors of the whole repository. A study written with other people needs their written consent to be licensed under that name, or its own repository with its own authors and copyright line.
- **Another license.** Everything here is MIT for code and CC BY 4.0 for the rest.
- **Size.** GitHub refuses files over 100 MB and warns from 50 MB; a repository should stay well under 1 GB. Larger data goes to Zenodo directly, with this repository linking to it.
- **A DOI of its own.** A version DOI here covers the whole repository. A study that will be cited on its own, for example in a paper, is easier to cite from its own record.

## The folder

Name the folder after the article's slug on the blog. Inside it:

- `README.md`, described below.
- The data files, with the columns explained in the README.
- The scripts that produce the published numbers, with the output they printed committed next to them (for example `results/summary.txt`). Prefer the standard library; when a dependency is needed, pin it in `requirements.txt`.
- `screenshots/`, if the article shows any, with the article's file names.

Add a row for the folder to the table in the root `README.md`.

## The folder's README

Follow the existing folders. The README should have:

- A first paragraph naming the article. Link it only once it is published: no link in this repository may return 404. Until then, give the title in italics and say the article isn't published yet.
- **Quick start**: the commands that reproduce the committed output, and the Python version they need. Run them on that version before writing it down.
- What each file holds, what the columns mean and how the data was collected, with dates in UTC.
- **Caveats**: what the data can't show.
- **How to cite**: the folder in the form the other folders use (`Markau, A., & DMARKOFF. (year). Title [Data set]. GitHub. URL`) and the article once it is published. Credit any list or dataset the study builds on, the way the census folder credits Tranco.

## What not to publish

- Addresses of test recipients, such as seed mailboxes, in files, file names or screenshots. Replace their domains with labels when the domain identifies the service, as `broken-spf-records-mailbox-providers` does with `*.seed.example`.
- Keys, tokens, passwords and internal host names, including inside logs and screenshots.
- Per-domain findings that point to something exploitable, such as an SPF include of a domain anyone can register. Publish aggregates instead.
- Text copied from other vendors' tools. A screenshot is enough.

Check the screenshots by eye, and check everything that was ever committed to the branch, not only the final files: history stays public after a file is deleted.

## Licensing

Nothing needs to be added per folder. The root README's License section covers new folders: MIT for `*.py` and `*.sql`, CC BY 4.0 for everything else, with the two exceptions there (screenshots, and content produced by other systems). If a new folder contains something that fits neither, such as a file under another license, say so in that folder's README and add a line to the root README's License section.

## Checks before opening the pull request

- Run `gitleaks git . --log-opts="--all"` from the repository root. `.gitleaks.toml` already allowlists verification tokens in other domains' TXT records and the published rua address; add to it only with a comment that says why.
- Run the Quick start in a clean environment and compare the output with the committed files byte by byte.
- Open every link in the new and changed README files.
- Make sure the pull request doesn't change data or result files of other folders. Corrections to published data go in their own pull request, described below.

## Changing published data

Don't rename, move or delete published files; the blog and other sites link to them. Corrections and late additions, such as aggregate reports that arrived after an article came out, are added to the existing files with a note in the folder's README saying what changed and when. If an article quotes a number the change affects, say in the README whether the article's number still holds.

## Releasing

Each release is archived on Zenodo, which gives it a version DOI; the concept DOI in the README badge always resolves to the latest release.

1. In the pull request, update `version` and `date-released` in `CITATION.cff`, plus `abstract`, `keywords` and `references` if the new folder needs it. Versions: a new folder is a minor release (1.1.0); corrections and late additions to existing folders are a patch release (1.0.1). Run `cffconvert --validate`.
2. Merge, then publish a GitHub release on `main` the same day, so `date-released` matches:

   ```sh
   gh release create v1.1.0 --target main --title "v1.1.0" --notes "Adds data for <article title>."
   ```

   Zenodo picks up published releases only, not tags.
3. Check the new version on Zenodo and fix it with Edit, then Publish. Zenodo reads only part of `CITATION.cff`, so look at least at:
   - Resource type: Dataset.
   - Licenses: CC BY 4.0 and MIT.
   - Related works: "Is supplement to" with the URL of each published article, and "Cites" with the DOI of each paper or dataset the study builds on.
   - Copyright, Languages and Dates (Collected) as on the previous version.

   Editing metadata doesn't create a new version or change a DOI. The files of a published version can't be changed; a fix is a new release.
