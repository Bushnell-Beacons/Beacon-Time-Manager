# Beacon Time Manager

A free static weekly planner for Bushnell student-athletes, using the selected warm ivory/gold design. Students use one dashboard with an editable daily agenda, personal activities/colors, goals, reminders, university dates, saved official competitions, KJV daily scripture, a yearly reading plan, and downloadable print layouts.

Review site: https://jmiyazawa4.github.io/Beacon-Time-Manager/

The GitHub Pages site now uses **Save on this device**: entries stay in this browser after reload or closing. Private session is optional and removes saved planner entries. Nothing syncs across devices; clearing browser/site data removes the planner. It is a review version, not a school-approved student release. No paid hosting, Python runtime, Bible API, or live athletics service is required by the deployed site. GitHub Pages is sufficient for this static public-repository site within its service limits. A custom domain is optional and is not being purchased.

## Included content

- **Sports:** saved official season schedules for all 15 sports offered in the selector. Each snapshot includes its official source URL and capture timestamp. The UI shows the last update. These are not live: postponements, cancellations, new seasons, and other changes require a manual snapshot update and republish. Confirm changes with athletics.
- **Academic calendar:** 54 deduplicated entries transcribed from the 2026–2027 calendar supplied by the project owner. Full-term and subterm deadlines are labeled. The “Show university dates” checkbox saves each student’s choice. When off, academic events and break shading are hidden from the calendar, agenda, and PDF exports; holidays remain shaded regardless of this choice, and the reference list below the calendar stays available. It starts on for existing behavior. Holidays are gold, breaks blue. Details are collapsed below the calendar and separately within the daily agenda. Shared dates persist across sports and appear in PDFs. Shading does not cancel personal recurring classes.
- **Bible:** 80 curated KJV passages about encouragement, peace, faith, and perseverance, rotated across the year independently of the M’Cheyne reading plan. KJV is public domain in the United States. The verse and four reading references are selected by the device's local date. Review the [curated passage list](beacon-planner/VERSE_SELECTIONS.md) to request keeps, removals, or replacements. February 29 is a catch-up day; March dates do not shift in leap years. Reading links open KJV on Bible Gateway only when clicked; the app makes no automatic Bible-service requests.
- **Reading-plan attribution:** passage-reference data is adapted from [willswire/mcheyne](https://github.com/willswire/mcheyne), exact commit and transformation notes in `reading-plan.json`, Apache-2.0 license included. KJV selections use [thiagobodruk/bible](https://github.com/thiagobodruk/bible), pinned source and MIT license included in `daily-verses.json`. No NIV text is included. Review territorial KJV publication rights if targeting jurisdictions outside the United States.

University dates retain inclusive range ends using an exclusive stored `end`. Thanksgiving includes November 26–27, 2026; spring break includes March 22–28, 2027, with Good Friday shaded as a holiday. The Summer 2027 commencement date of December 10, 2027 is preserved exactly as supplied. Session 2 add/drop asterisks retain a note because their footnote was not supplied. These dates were checked against the owner-provided text, not independently fetched from the blocked university page.

## Editing and privacy

Click an empty time or **Add activity** to create a class; click a block to edit its name, times, recurring days, and color. Text contrast adjusts automatically. The daily agenda uses the same editable entries. No student-facing view/theme switcher or JSON backup controls are present.

Personal entries stay in this browser profile. Normal mode uses unencrypted localStorage; private-session mode avoids saving and clears on reload/page exit. Other open tabs are told to stop saving after private mode is enabled. Shared computers and downloaded PDFs still require care. See [SECURITY.md](SECURITY.md) for the actual protections and limitations.

`.ics` and `.csv` files are parsed locally, never uploaded. Choose a sport, click the visible Import CSV button, and set the CSV year in Schedule details & import when dates omit it. The dedicated picker has no file-type filter to avoid platform-specific CSV files being grayed out; the app validates the .csv extension after selection. Imports open the first week of the file automatically. CSV supports Date, Event/Title, Duration (a time range), Location, Required Attendance, and Description; separate Start Time/End Time columns also work with AM/PM or 24-hour times. Dates support YYYY-MM-DD, MM/DD/YYYY, or month/day labels. Exact ranges use Pacific time; incomplete or ambiguous times remain dated notes marked for confirmation. A confirmation shows entry/review/skipped counts before import. Attendance groups are displayed as labels, not automatically assigned to students. Only the selected student browser receives imported entries; no uploaded CSV is bundled with the public site. Limits: 2 MB, 2,000 events, 40,000 lines. UTC and IANA timezones are supported; floating times use Pacific time and DST. All-day dates stay fixed. Recurring ICS rules/exceptions and custom timezone definitions are skipped. Cross-midnight timed events currently show only their start day through midnight. Unpublished game durations use sport-specific planning estimates, visibly marked “est.” in the calendar, agenda, and PDFs; TBA games remain above the grid. Estimates exclude warm-ups and travel. See [duration research](beacon-planner/sports-duration-research.json) for samples, limits, and provisional values. Overlapping scheduled hours are counted separately.

Completing a goal triggers a five-second confirmation and a short navy/gold confetti burst; unchecking, rendering, or reloading a completed goal does not trigger it. Reduced-motion preferences disable confetti, and no audio plays.

After the latest timed official game for the selected sport finishes, a personal check-in asks how it went. Published end times take precedence; otherwise the sport’s planning duration estimates the finish. Cancelled, postponed, TBA/all-day, future, and more-than-72-hour-old games do not prompt. The page checks once a minute while open and when revisited/visible. Win gives a celebration, loss gives encouragement, and tie gives a reflection message. Students can change an answer before closing, snooze for one hour (also via Escape before answering), or skip. Answers and snoozes are stored only in the existing browser-local planner state; private mode keeps them only for that page session. These are self-reports, not official/live scores, and are not published to other students. No score-update service or owner-provided results file is required.

Reminders support Low/Normal/High importance and a custom color stripe, with text labels so importance does not depend on color. Edit preserves the reminder instead of duplicating it; older entries default to Normal. Choices save in the same browser unless Private session is on. Reminders work while the page is open. Browser notifications are optional and use generic text instead of reminder contents. No cloud sync, student-account database, analytics, or automatic sharing is included.

## PDFs

**Print / Download** exports the displayed week as a compact landscape grid, portrait agenda, or daily pages with writing space. US Letter/A4, grayscale, and an optional KJV verse are available. Compact-grid labels may shorten; agendas retain full names and can continue onto extra pages. PDFs are generated on-device. jsPDF 4.2.1 is vendored with its MIT license; no CDN or package installation is needed by the reader.

## Maintainer workflow

Python is only needed for optional local development and manual content refreshes, not by students or GitHub Pages. From `beacon-planner`, `python server.py` serves an optional loopback development site. Python 3.10+ with the IANA timezone database is supported; Python 3.12 was tested.

Refresh one sport or all sports, inspect the changes, then test and rebuild:

```sh
python tools/update_schedules.py --sport baseball
# Omit --sport to update all sports; the official crawl delay makes this several minutes.
python tools/build_browser_preview.py --save-on-device --output /path/to/publish/index.html
```

The update script only reads official allowlisted sports pages, checks robots rules, and waits at least 30 seconds between source requests. Failed/unverified refreshes retain older files. The snapshot adapter joins the visible competition date/time with its year from structured metadata; this avoids a verified AM/PM error in the source's JSON-LD. Format changes need maintenance. Source IDs deduplicate refreshes and preserve personal classes. Matching calendar imports are suppressed when an official competition is already present; distinct official IDs remain separate to preserve doubleheaders. Each timed event renders as one continuous block, with stable columns for overlaps. Goals and reminders sit above the calendar, and the sport question is compact.

The `gh-pages` branch publishes only a self-contained `index.html` and `.nojekyll`, with optional private sessions, browser-local saving, and a meta CSP. `--hosted-preview` remains available for a separate locked, non-saving review build. Push updates to that branch to refresh the same public URL. The builder embeds assets, content, and license texts; it does not deploy Python or expose source/config files. A school-approved student release needs a separate privacy/security decision about saving, origin, contact/operations, and provider settings.

## Verification

```sh
python -m unittest discover -s beacon-planner/tests -v
node beacon-planner/tests/calendar_import.test.js
node beacon-planner/tests/csv_import.test.js
node beacon-planner/tests/privacy_storage.test.js
node beacon-planner/tests/reading_plan.test.js
node beacon-planner/tests/sports_events.test.js
```

Optional browser checks need Python Playwright and `/usr/bin/chromium`. Run with a local server and set `BEACON_TEST_URL` if necessary:

```sh
python beacon-planner/tests/browser_features.py
python beacon-planner/tests/browser_reminders.py
python beacon-planner/tests/browser_celebrations.py
python beacon-planner/tests/browser_sports_blocks.py
python beacon-planner/tests/browser_academic_dates.py
python beacon-planner/tests/live_schedule_smoke.py
python beacon-planner/tests/browser_privacy_security.py
python beacon-planner/tests/browser_hosted_preview.py
```

`live_schedule_smoke.py` keeps its historical filename but now verifies saved files only; it does not call athletics. Tests cover date/time correctness, shared holidays, collapsed academic details, KJV/leap-year rotation, real saved competition rendering, class editing, mobile widths, all PDF layouts, hostile import text, no personal uploads, and private sessions. Fixture dates/passages are explicitly labeled and are not shipped as official content.
