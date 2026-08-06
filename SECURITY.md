# Security Policy

Thanks for helping keep Browser Tab Counter safe. This is a small, free,
open-source macOS utility maintained by one person, and reports are genuinely
welcome.

## Reporting a vulnerability

**Please report privately, not in a public issue.**

👉 **[Report a vulnerability](https://github.com/mariolonghi/browser-tab-counter/security/advisories/new)**
— or go to the repo's **Security** tab → **Report a vulnerability**.

That uses GitHub's private vulnerability reporting: only you and the maintainer
can see it, we can discuss a fix privately, and a credited advisory can be
published once it's resolved. You don't need my email address, and nothing is
exposed while we work on it.

*If you can't use that form for some reason,* open a public issue that says only
that you've found a security problem and would like a private channel — **no
details**, please — and I'll open one.

### What to include

Whatever you have. Most useful:

- What an attacker can achieve, and what they'd need first (already on the Mac?
  a malicious website? a compromised network?)
- Steps to reproduce, ideally on a specific version (the About panel shows it)
- Your macOS version and which browsers were involved

### What to expect

I'll acknowledge within about a week and give you an honest assessment: whether
I can reproduce it, whether I consider it in scope, and roughly when a fix
might ship. This is a hobby project with limited support, so please don't
expect an enterprise SLA — but I take real security issues seriously and will
say so plainly if I can't or won't fix something.

Fixes ship as a normal notarized release, and the in-app updater brings existing
users along. Serious issues get a published advisory crediting you (unless you'd
rather stay anonymous).

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest release | ✅ |
| Anything older | ❌ — please update first |

The app self-updates from the About panel, so "update to the latest release and
see if it still happens" is a reasonable first step.

## Scope

The app's whole job is to read *how many* tabs are open. It has no server, no
account, no telemetry, and stores only a small settings file and a counts-only
history locally. That keeps the interesting attack surface small and specific.

### In scope — these are the ones I care about most

- **The self-updater** ([`src/selfupdate.py`](src/selfupdate.py)) — anything that
  gets an unverified, tampered, downgraded or attacker-supplied bundle installed.
  It's meant to install *only* a build that is notarized **and** signed by Team
  ID `ZWXAL8XA46`, downloaded over HTTPS from GitHub, and to **fail closed** when
  it can't verify. Breaking any of that is a real finding.
- **The release pipeline** — anything letting someone publish or substitute a
  release artifact, or extract the signing secrets from CI.
- **Code execution or injection from browser-supplied data.** Tab titles and
  URLs are untrusted input. The exported HTML report escapes them and only
  linkifies `http(s)`, and the Firefox session decoder is bounds-checked — if you
  get past either, that's in scope.
- **Reading or transmitting anything beyond the stated behaviour** — e.g. tab
  content leaving the machine, or data written outside
  `~/Library/Application Support/BrowserTabCounter/` and files you chose to save.
- **Privilege escalation or permission (TCC) bypass** via the app.

### Out of scope

- **The Automation permission itself.** The app asks macOS for permission to read
  each browser, and you grant it. That's the documented design, not a flaw.
- **Tab titles/URLs appearing in an export you explicitly asked for.** The
  export is on-demand and writes only where you choose.
- **Reading Firefox's own session file** to count its tabs — documented, local,
  read-only.
- **Old versions** — please reproduce on the latest release.
- Issues in **macOS, browsers, or third-party dependencies** themselves (report
  those upstream; do tell me if the app uses them unsafely).
- Anything needing **physical access, an already-compromised Mac, or social
  engineering**.
- Missing hardening with no demonstrated impact, and automated-scanner output
  without a working scenario.

## Safe harbour

If you make a good-faith effort to follow this policy, I won't pursue or support
any action against you for your research. Please only test against your own
machine and your own installation, don't access anyone else's data, and give me
a reasonable chance to fix things before disclosing publicly.

## What's already in place

For context on what's been done (and what a report would be measured against):

- Releases are **Developer ID signed, notarized and stapled**; the updater
  verifies signature integrity, notarization *and* the pinned Team ID before
  installing, and refuses to install if it cannot verify.
- Update downloads are HTTPS-only, restricted to GitHub hosts, and size-capped.
- CI secrets are scoped to the single step that needs them, and the third-party
  release action is pinned to a commit SHA.
- Secret scanning, push protection and Dependabot alerts are enabled.
- The codebase has had two full security reviews; findings and fixes are
  summarised in the release notes.
