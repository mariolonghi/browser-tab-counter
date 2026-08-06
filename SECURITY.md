# Security Policy

## Found a security problem? Tell me privately.

👉 **[Report a vulnerability](https://github.com/mariolonghi/browser-tab-counter/security/advisories/new)**

Or: repo → **Security** tab → **Report a vulnerability**.

**Please don't open a public issue for a security bug.** The private form keeps
it between you and me until there's a fix. You don't need my email address.

*Can't use the form? Open a public issue saying only that you've found a
security problem and want a private channel. No details. I'll open one.*

### What to send

- What an attacker could do, and what they'd need first
- Steps to reproduce
- App version (see the About panel), your macOS version, which browsers

Rough notes are fine. Send what you have.

### What happens next

- I'll reply within about a week.
- I'll tell you straight: can I reproduce it, is it in scope, when might a fix ship.
- Fixes go out as a normal release. The app updates itself.
- Serious bugs get a published advisory crediting you, unless you'd rather not.

This is a free, one-person project. I take real security bugs seriously, but
there's no enterprise support desk behind it.

### Versions

Only the **latest release** is supported. Please update first and check whether
the bug is still there.

---

## Details

Useful if you're deciding whether something is worth reporting.

### The app in one paragraph

It reads *how many* tabs are open in your browsers and shows the number in the
menu bar. No server, no account, no telemetry. It stores a small settings file
and a counts-only history in
`~/Library/Application Support/BrowserTabCounter/`, plus any file you explicitly
export. That keeps the attack surface small and specific.

### What I most want to hear about

- **The self-updater** ([`src/selfupdate.py`](src/selfupdate.py)). It should
  install *only* a build that is notarized **and** signed by Team ID
  `ZWXAL8XA46`, fetched over HTTPS from GitHub — and it should **refuse to
  install** when it can't verify that. Anything that gets a tampered,
  downgraded, unverified or attacker-supplied bundle installed is a real
  finding.
- **The release pipeline.** Anything that lets someone publish or swap a release
  artifact, or pull the signing secrets out of CI.
- **Code execution or injection from browser data.** Tab titles and URLs are
  untrusted input. The HTML export escapes them and only linkifies `http(s)`;
  the Firefox session decoder is bounds-checked. Get past either and I want to
  know.
- **Data going somewhere it shouldn't.** Anything leaving the machine, or
  written outside the paths above.
- **Permission (TCC) bypass or privilege escalation** through the app.

### What isn't a security bug

- **The Automation permission.** The app asks macOS to read your browsers and
  you approve it. That's the design.
- **Tab titles and URLs in an export you asked for.** It runs on demand and
  writes only where you choose.
- **Reading Firefox's session file** to count its tabs. Documented, local,
  read-only.
- **Old versions.** Reproduce on the latest release.
- **Bugs in macOS, browsers, or dependencies themselves.** Report those
  upstream — though do tell me if this app uses them unsafely.
- Anything needing **physical access, an already-compromised Mac, or social
  engineering**.
- Missing hardening with no demonstrated impact, or scanner output with no
  working scenario.

### Safe harbour

Follow this policy in good faith and I won't pursue anything against you for
your research. Test only your own machine and your own installation, don't touch
anyone else's data, and give me a fair chance to fix things before going public.

### What's already in place

So you know what you're testing against:

- Releases are **Developer ID signed, notarized and stapled**. The updater
  checks signature integrity, notarization *and* the pinned Team ID before
  installing, and fails closed if it can't.
- Update downloads are HTTPS-only, restricted to GitHub hosts, and size-capped.
- CI secrets are scoped to the one step that needs them; the third-party release
  action is pinned to a commit SHA.
- Secret scanning, push protection and Dependabot alerts are on.
- The codebase has had two full security reviews.
