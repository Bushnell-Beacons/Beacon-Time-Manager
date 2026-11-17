import sys
import unittest
from pathlib import Path
from time import monotonic
from unittest.mock import patch
from urllib.robotparser import RobotFileParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import schedule_source as source
FIXTURES = Path(__file__).parent / 'fixtures'


class ScheduleSourceTests(unittest.TestCase):
    def fixture(self, sport='baseball'):
        return (FIXTURES / (sport + '.html')).read_text()

    def test_visible_time_overrides_incorrect_json_ampm(self):
        result = source.parse_schedule(self.fixture(), 'official')
        self.assertEqual(len(result['events']), 3)
        self.assertEqual(result['skipped'], 0)
        redwoods = next(e for e in result['events'] if e['id'] == '7467')
        self.assertEqual(redwoods['start'], '2026-10-10T11:00:00-07:00')
        self.assertEqual(redwoods['sourceUrl'], 'official')
        self.assertIsNone(redwoods['end'])

    def test_ranked_basketball_and_volleyball_opponents(self):
        for sport in ['mens-basketball', 'womens-volleyball']:
            with self.subTest(sport=sport):
                result = source.parse_schedule(self.fixture(sport), 'official')
                self.assertEqual(len(result['events']), 3)
                self.assertEqual(result['skipped'], 0)

    def test_unpublished_time_has_no_invented_start_hour(self):
        result = source.parse_schedule(self.fixture(), 'official')
        event = result['events'][-1]
        self.assertTrue(event['timeUnknown'])
        self.assertEqual(event['start'], '2027-05-28')
        self.assertNotIn('T', event['start'])
        self.assertEqual(event['end'], '2027-06-06')
        self.assertEqual(event['timeLabel'], 'TBD')

    def test_cancellation_preserved(self):
        html = self.fixture().replace('</li>', '<div class="sidearm-schedule-game-result">Canceled</div></li>')
        result = source.parse_schedule(html, 'official')
        self.assertTrue(all(e['status'] == 'CANCELLED' for e in result['events']))

    def test_unverifiable_page_fails_instead_of_inventing_events(self):
        with self.assertRaises(ValueError):
            source.parse_schedule('<html>Schedule changed</html>', 'official')
        html = self.fixture().replace('application/ld+json', 'text/plain')
        with self.assertRaises(ValueError):
            source.parse_schedule(html, 'official')

    def test_resolved_playoff_opponent_uses_own_full_date_label(self):
        # Synthetic minimal case; this is not shipped as an official game.
        html = '<script type="application/ld+json">[{"@type":"SportsEvent","name":"Bushnell Vs NBA 2K Playoffs","startDate":"2026-11-17T17:00:00"}]</script>'
        html += '<li class="sidearm-schedule-game" data-game-id="playoff"><div class="sidearm-schedule-game-opponent-name">Post University</div><div class="sidearm-schedule-game-opponent-date"><span>Nov 17 (Tue)</span><span>7 p.m.</span></div><a aria-label="Watch Video for Esports vs Post University on November 17, 2026 at 7 p.m.">Watch</a></li>'
        result = source.parse_schedule(html, 'official')
        self.assertEqual(result['skipped'], 0)
        self.assertEqual(result['events'][0]['start'], '2026-11-17T19:00:00-08:00')
        self.assertEqual(result['events'][0]['title'], 'Post University')
        # A different opponent/date is not acceptable evidence for this game.
        for changed in [html.replace('on November 17, 2026', 'on November 18, 2026'), html.replace('vs Post University on', 'vs Another College on')]:
            with self.assertRaises(ValueError):
                source.parse_schedule(changed, 'official')
        conflict = html.replace('NBA 2K Playoffs', 'Post University').replace('on November 17, 2026', 'on November 17, 2027')
        with self.assertRaises(ValueError):
            source.parse_schedule(conflict, 'official')

    def test_cache_reuses_result_and_checks_robots(self):
        policy = RobotFileParser()
        policy.parse(['User-agent: *', 'Allow: /'])
        with patch.object(source, '_robots', policy), patch.object(source, '_robots_checked', monotonic()), patch.object(source, '_cache', {}), patch.object(source, '_request', return_value=self.fixture()) as request:
            first = source.load_official_schedule('baseball')
            second = source.load_official_schedule('baseball')
            self.assertEqual(first, second)
            request.assert_called_once()
            self.assertEqual(first['source'], 'https://bushnellbeacons.com/sports/baseball/schedule')

    def test_robots_disallow_blocks_fetch(self):
        policy = RobotFileParser()
        policy.parse(['User-agent: *', 'Disallow: /sports/'])
        with patch.object(source, '_robots', policy), patch.object(source, '_robots_checked', monotonic()), patch.object(source, '_cache', {}), patch.object(source, '_request') as request:
            with self.assertRaises(ValueError):
                source.load_official_schedule('baseball')
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
