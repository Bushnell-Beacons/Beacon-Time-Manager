"""Read public Sidearm schedule pages; never infer games or use private APIs."""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
from threading import Lock
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
import json
import re

PACIFIC = ZoneInfo('America/Los_Angeles')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag='', attrs=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), []

    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def by_class(self, name):
        return next((n for n in self.walk() if name in n.attrs.get('class', '').split()), None)


class ScheduleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def normalized(text):
    return re.sub(r'^(?:#\d+\s*|rv\s+)', '', ' '.join(text.casefold().split()))


def parse_schedule(html, source):
    parser = ScheduleHTML()
    parser.feed(html)
    nodes = list(parser.root.walk())
    structured = []
    for node in nodes:
        if node.tag == 'script' and node.attrs.get('type') == 'application/ld+json':
            try:
                data = json.loads(''.join(c for c in node.children if isinstance(c, str)))
                structured.extend(data if isinstance(data, list) else data.get('@graph', [data]))
            except (ValueError, TypeError, AttributeError):
                continue
    games = [n for n in nodes if 'sidearm-schedule-game' in n.attrs.get('class', '').split() and n.attrs.get('data-game-id')]
    if not games:
        raise ValueError('The official schedule page has no supported competition entries')
    events, skipped = {}, 0
    for game in games:
        try:
            opponent_node = game.by_class('sidearm-schedule-game-opponent-name')
            dates_node = game.by_class('sidearm-schedule-game-opponent-date')
            if opponent_node is None or dates_node is None:
                raise ValueError('Missing opponent or date')
            opponent = opponent_node.text()
            spans = [n.text() for n in dates_node.children if isinstance(n, Node) and n.tag == 'span']
            match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})', spans[0])
            month = datetime.strptime(match[1], '%b').month
            day = int(match[2])
            # Only the year is taken from JSON-LD. Its AM/PM values can disagree
            # with the visible schedule (verified on the official baseball page).
            years = set()
            for item in structured:
                if not isinstance(item, dict) or item.get('@type') != 'SportsEvent':
                    continue
                try:
                    start = date.fromisoformat(str(item.get('startDate', ''))[:10])
                except ValueError:
                    continue
                if start.month == month and start.day == day and normalized(opponent) in normalized(item.get('name', '')):
                    years.add(start.year)
            # Newly resolved playoff opponents can be missing from stale JSON-LD.
            # A full date on a link inside this same game is also first-party
            # evidence, provided it names this opponent and matches the visible day.
            explicit_years = set()
            for node in game.walk():
                label = node.attrs.get('aria-label', '')
                if not opponent or normalized(opponent) not in normalized(label):
                    continue
                for full in re.finditer(r'\bon\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b', label, re.I):
                    try:
                        label_month = datetime.strptime(full[1][:3], '%b').month
                        labelled = date(int(full[3]), label_month, int(full[2]))
                    except ValueError:
                        continue
                    if labelled.month == month and labelled.day == day:
                        explicit_years.add(labelled.year)
            if years and explicit_years and years != explicit_years:
                raise ValueError('Conflicting competition years')
            if not years:
                years = explicit_years
            if len(years) != 1:
                raise ValueError('Missing or ambiguous competition year')
            on = date(years.pop(), month, day)
            end_date = None
            labels = spans[1:]
            if labels and re.match(r'^[A-Za-z]{3}\s+\d', labels[0]):
                finish_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})', labels[0])
                finish_month = datetime.strptime(finish_match[1], '%b').month
                finish_day = int(finish_match[2])
                finish_year = on.year + ((finish_month, finish_day) < (on.month, on.day))
                end_date = (date(finish_year, finish_month, finish_day) + timedelta(days=1)).isoformat()
                labels = labels[1:]
            time_label = ' '.join(labels).strip()
            clock = re.fullmatch(r'(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?(?:\s*\(?([A-Z]{2,3})\)?)?', time_label, re.I)
            all_day = not bool(clock)
            if clock:
                hour, minute = int(clock[1]), int(clock[2] or 0)
                if not 1 <= hour <= 12 or not 0 <= minute <= 59:
                    raise ValueError('Invalid official start time')
                suffix = (clock[4] or 'PT').upper()
                zones = {'PT': 'America/Los_Angeles', 'PST': 'America/Los_Angeles', 'PDT': 'America/Los_Angeles',
                         'ET': 'America/New_York', 'EST': 'America/New_York', 'EDT': 'America/New_York',
                         'CT': 'America/Chicago', 'CST': 'America/Chicago', 'CDT': 'America/Chicago',
                         'MT': 'America/Denver', 'MST': 'America/Denver', 'MDT': 'America/Denver'}
                if suffix not in zones:
                    raise ValueError('Unknown official timezone')
                start = datetime(on.year, on.month, on.day, hour % 12 + (12 if clock[3].lower() == 'p' else 0), minute, tzinfo=ZoneInfo(zones[suffix])).isoformat()
            else:
                start = on.isoformat()
            text = game.text().casefold()
            cancelled = bool(re.search(r'\bcancel(?:led|ed)\b', text))
            postponed = 'postponed' in text
            location = game.by_class('sidearm-schedule-game-location')
            uid = game.attrs['data-game-id']
            events[uid] = {'id': uid, 'title': ('Postponed: ' if postponed else '') + opponent,
                           'start': start, 'end': end_date if all_day else None, 'allDay': all_day, 'timeUnknown': all_day,
                           'timeLabel': time_label or 'Time TBA', 'status': 'CANCELLED' if cancelled else 'POSTPONED' if postponed else '',
                           'location': location.text() if location is not None else '', 'sourceUrl': source,
                           'timeZoneNote': 'Times without a zone are interpreted in Pacific time. Confirm with the official schedule.'}
        except (ValueError, IndexError, TypeError, AttributeError):
            skipped += 1
    if not events:
        raise ValueError('Competition dates could not be verified from the official page')
    return {'events': list(events.values()), 'skipped': skipped,
            'note': 'From the official athletics schedule. Times without a zone are interpreted in Pacific time; confirm changes with athletics. Event durations are not published.'}

# Process-wide cache and crawl budget keep repeated sport selection from
# repeatedly requesting the athletics site. Nothing student-specific is sent.

AGENT = 'BeaconStudentPlanner/1.0 (educational scheduling)'
BASE = 'https://bushnellbeacons.com'
_cache = {}
_lock = Lock()
_robots = None
_robots_checked = 0
_next_request = 0
_delay = 30


def _request(url, limit):
    global _next_request
    sleep(max(0, min(30, _next_request - monotonic())))
    try:
        with urlopen(Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,text/plain'}), timeout=15) as response:
            raw = response.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('Official schedule response exceeds the supported size')
            return raw.decode('utf-8-sig')
    finally:
        _next_request = monotonic() + _delay


def load_official_schedule(sport):
    global _robots, _robots_checked, _delay
    sport = {'volleyball': 'womens-volleyball'}.get(sport, sport)
    source = BASE + '/sports/' + sport + '/schedule'
    with _lock:
        cached = _cache.get(sport)
        if cached and monotonic() - cached[0] < 900:
            return cached[1]
        if _robots is None or monotonic() - _robots_checked >= 3600:
            policy = RobotFileParser(BASE + '/robots.txt')
            try:
                policy.parse(_request(BASE + '/robots.txt', 128_000).splitlines())
            except HTTPError as error:
                if error.code != 404:
                    raise ValueError('Unable to verify athletics site access rules') from error
                policy.parse([])
            requested_delay = policy.crawl_delay(AGENT) or policy.crawl_delay('*') or 30
            if requested_delay > 30:
                raise ValueError('The athletics site requires a longer crawl interval than this integration supports')
            _delay = max(30, requested_delay)
            _robots, _robots_checked = policy, monotonic()
        if not _robots.can_fetch(AGENT, source):
            raise ValueError('The athletics site does not allow automated access to this schedule')
        result = parse_schedule(_request(source, 4_000_000), source)
        result.update(source=source, fetchedAt=datetime.now(timezone.utc).isoformat())
        _cache[sport] = (monotonic(), result)
        return result
