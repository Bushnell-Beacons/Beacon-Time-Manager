# Security and privacy status

This is a security baseline, not a guarantee against breaches or a compliance certification. The deployed GitHub Pages site supports browser-local saving, with optional Private session for shared computers. Saved entries remain after reload/closing in the same browser profile; clearing site data erases them. This is not cloud backup or device sync.

## Data flows

| Content | Handling |
| --- | --- |
| Names/nicknames, classes, goals, reminders, game check-in answers | Browser only. Saving uses unencrypted localStorage in this browser profile. Private session keeps entries only in page memory. |
| Imported ICS/CSV files | Parsed locally. Files and filenames are not uploaded. |
| Sports, academic dates, KJV verses, reading references | Included public files. No live API calls, student-specific requests, or paid data services. |
| PDF exports | Created on-device; they contain schedule information and remain wherever the user saves/shares them. |
| Hosting metadata | GitHub Pages can receive IP/request metadata. Provider policies and administrative access still need review. |
| External links | Official sources and KJV passage pages are opened only when a user chooses a link. No-referrer settings reduce disclosure of the page address. |

There are no student accounts, public profiles, cloud sync, analytics, trackers, or automatic sharing. Names are optional; a nickname is sufficient. Avoid IDs, grades, health information, and information about other students. Notifications are opt-in and contain generic text.

## Implemented protections

- The self-contained hosted build has a meta Content Security Policy allowing only exact bundled script hashes, inline styling, and data/blob images. It blocks automatic network connections, unapproved scripts, objects, base overrides, and form submissions. The static preview has no backend endpoints or uploaded assets.
- The optional local/WSGI server also supplies security headers, including framing denial, no-referrer, nosniff, origin isolation, and restricted camera/microphone/location permissions. GitHub Pages does not apply that Python server's headers: notably, `frame-ancestors` cannot be enforced using a meta CSP alone.
- Optional server file delivery uses an explicit allowlist, denies source/configuration/tests and traversal, and rejects writes without reading bodies. All live API routes are removed. It does not fetch external content when students use it.
- Imported calendar HTML remains text. Files, lines, events, field lengths, timezone/date formats, and invalid DST times are bounded/validated. Embedded URLs and attachments are not fetched.
- CSV fields are treated as text; imports have row/size limits and confirm counts before applying. Ambiguous times are not inferred.
- Private sessions delete this app's durable planner entry and stop saving. Other open tabs receive the mode change. Storage failures report that older data may remain. Existing downloads, screenshots, backups, restored browser state, or copies outside this app cannot be erased by the feature.
- A separate `--hosted-preview` build can lock private mode; the deployed `--save-on-device` build permits local saving. GitHub project sites share an owner's origin; this remains a reason to review hosting/origin choices before a real student rollout, even when the public GitHub address is retained.
- PDFs are generated locally with pinned, vendored jsPDF. KJV data and reading-plan reference licenses/attribution are included. No remote publisher script executes in the planner.

## Before student rollout

Have the university review the data handling, hosting/origin, provider logging/retention, administrative access and MFA, accessibility, contact/reporting route, and ongoing content/dependency maintenance. Verify HTTPS and provider settings on the actual deployed address. Do not claim school approval, FERPA compliance, encryption of browser storage, or zero risk based on these changes.

The free static architecture does not require paid hosting or a Python backend. A school subdomain is optional and needs IT approval; GitHub Pages can continue to host the files. Source schedule changes must be checked and republished manually. Student-only access, future accounts/rosters, or cloud sync would require a new authentication, authorization, retention, and encrypted-storage design.

`requirements-production.txt` and `gunicorn.conf.py` are only optional for an institution choosing to self-host the static files with the additional HTTP headers. They are not used by GitHub Pages. Such a host must configure HTTPS/redirects, exact `BEACON_ALLOWED_HOSTS`, HSTS (`BEACON_HTTPS=1` behind a real HTTPS proxy), resource controls, logs, and operations. Server error/proxy logs may include connection metadata.

## Evidence

Unit, Node, and browser tests exercise real CSP enforcement, inert hostile imports, no private-marker uploads, local-only calendar parsing, private sessions across tabs/reload, notification privacy, static saved schedules, yearly KJV rotation, holiday boundaries, mobile layouts, and actual PDF downloads. The GitHub Pages review bundle is tested with all API/asset requests blocked except its initial HTML document. A third-party security audit and student-release approval have not been performed.
