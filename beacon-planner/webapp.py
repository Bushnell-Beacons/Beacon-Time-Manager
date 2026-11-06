"""Read-only HTTP/WSGI boundary. Personal planner data is never accepted here."""
from base64 import b64encode
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote, urlparse
import json
import mimetypes
import os
import re


ROOT = Path(__file__).resolve().parent
SPORTS = {'baseball','mens-basketball','womens-basketball','mens-soccer','womens-soccer',
          'volleyball','womens-volleyball','beach-volleyball','softball','mens-cross-country',
          'womens-cross-country','mens-track-and-field','womens-track-and-field','mens-golf','womens-golf','esports'}
PUBLIC_FILES = {'index.html','academic-calendar.js','academic-calendar.json','bible-verses.js',
                'calendar-import.js','csv-import.js','sports-events.js','privacy-storage.js','planner-views.css','planner-views.js',
                'schedule-pdf.js','celebrations.js','theme.css','reading-plan.json','daily-verses.json','vendor/jspdf.umd.min.js','assets/beacon-b.png','assets/tri-athlete-model.png'}


def security_headers():
    html = (ROOT / 'index.html').read_text()
    hashes = ["'sha256-" + b64encode(sha256(script.encode()).digest()).decode() + "'"
              for script in re.findall(r'<script>(.*?)</script>', html, re.S)]
    policy = "default-src 'self'; script-src 'self' " + ' '.join(hashes) + "; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; object-src 'none'; frame-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    headers = {'Content-Security-Policy': policy, 'X-Content-Type-Options':'nosniff',
               'X-Frame-Options':'DENY', 'Referrer-Policy':'no-referrer',
               'Cross-Origin-Opener-Policy':'same-origin', 'Cross-Origin-Resource-Policy':'same-origin',
               'Permissions-Policy':'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
               'Cache-Control':'no-store'}
    if os.environ.get('BEACON_HTTPS') == '1':
        headers['Strict-Transport-Security'] = 'max-age=31536000'
    return headers


def response(status, body, content_type='application/json', extra=None):
    if not isinstance(body, bytes):
        body = json.dumps(body, ensure_ascii=True).encode()
    headers = {**security_headers(), 'Content-Type':content_type, 'Content-Length':str(len(body))}
    if extra:
        headers.update(extra)
    return status, headers, body


def dispatch(method, target, headers):
    if len(target) > 2048:
        return response(414, {'error':'Request URL is too long'})
    host = headers.get('Host', '')
    try:
        if not re.fullmatch(r'[A-Za-z0-9.-]+(?::[0-9]{1,5})?', host):
            raise ValueError('Invalid host')
        hostname = urlparse('//'+host).hostname.lower()
    except (ValueError, AttributeError):
        return response(400, {'error':'Invalid host'})
    allowed = {'localhost','127.0.0.1'} | {h.strip().lower() for h in os.environ.get('BEACON_ALLOWED_HOSTS','').split(',') if h.strip()}
    if hostname not in allowed:
        return response(400, {'error':'Host is not configured for this site'})
    if method not in {'GET','HEAD'}:
        return response(405, {'error':'This server accepts no planner data or file uploads'}, extra={'Allow':'GET, HEAD'})
    url = urlparse(target)
    if url.path.startswith('/api/'):
        if method != 'GET':
            return response(405, {'error':'Use GET'}, extra={'Allow':'GET'})
        origin = headers.get('Origin')
        if headers.get('Sec-Fetch-Site') == 'cross-site' or (origin and urlparse(origin).netloc.lower() != host.lower()):
            return response(403, {'error':'Cross-site API requests are not allowed'})
        return response(404, {'error':'This site uses included data and has no live API'})
    name = 'index.html' if url.path == '/' else unquote(url.path).removeprefix('/')
    saved_schedule=name in {'schedules/'+sport+'.json' for sport in SPORTS}
    if name not in PUBLIC_FILES and not saved_schedule:
        return response(404, {'error':'Not found'})
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        return response(404, {'error':'Not found'})
    content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    if content_type.startswith('text/') or content_type in {'application/javascript','application/json'}:
        content_type += '; charset=utf-8'
    result = response(200, path.read_bytes(), content_type)
    return (result[0],result[1],b'') if method == 'HEAD' else result


def application(environ, start_response):
    """WSGI entry point for a production server; no request body is read."""
    headers = {'Host':environ.get('HTTP_HOST',''), 'Origin':environ.get('HTTP_ORIGIN',''),
               'Sec-Fetch-Site':environ.get('HTTP_SEC_FETCH_SITE','')}
    target = environ.get('PATH_INFO','/')
    if environ.get('QUERY_STRING'):
        target += '?' + environ['QUERY_STRING']
    try:
        status, outgoing, body = dispatch(environ.get('REQUEST_METHOD','GET'), target, headers)
    except Exception:
        # Return no stack trace, request text, or user data in a public response.
        status, outgoing, body = response(500, {'error':'The service is temporarily unavailable'})
    start_response(f'{status} {HTTPStatus(status).phrase}', list(outgoing.items()))
    return [body]
