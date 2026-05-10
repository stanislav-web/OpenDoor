# -*- coding: utf-8 -*-

"""Runtime shadow-copy probing for confirmed 200 OK file hits."""

import hashlib
import threading
from queue import Queue
from urllib.parse import urlsplit, urlunsplit

from src.core import CoreConfig
from src.core import helper


class ShadowProbe(object):
    """Bounded active probe worker for backup/shadow postfix copies."""

    BUCKET = 'shadow'
    MAX_CANDIDATES_PER_HIT = 12
    MAX_TOTAL_PROBES = 500
    MAX_BODY_SIZE = 1024 * 1024
    SHADOW_STATUSES = {200}
    QUEUE_TIMEOUT_SEC = 0.25

    SOURCE_EXTENSIONS = {
        'asp', 'aspx', 'bash', 'c', 'cfg', 'cgi', 'conf', 'config', 'cpp', 'cs',
        'css', 'env', 'go', 'h', 'hpp', 'htm', 'html', 'inc', 'ini', 'java',
        'js', 'json', 'jsx', 'jsp', 'kt', 'lua', 'md', 'php', 'phps', 'phtml',
        'pl', 'properties', 'py', 'pyw', 'rb', 'rs', 'sh', 'sql', 'toml', 'ts',
        'tsx', 'txt', 'xml', 'yaml', 'yml', 'zsh',
    }
    SPECIAL_FILENAMES = {
        '.env', '.env.local', '.env.production', '.env.staging', '.htaccess',
        '.htpasswd', 'composer.json', 'composer.lock', 'dockerfile',
        'docker-compose.yml', 'docker-compose.yaml', 'gemfile', 'gemfile.lock',
        'makefile', 'package.json', 'package-lock.json', 'pipfile',
        'pipfile.lock', 'procfile', 'pyproject.toml', 'requirements.txt',
        'settings.py', 'web.config', 'webpack.config.js', 'yarn.lock',
    }
    BINARY_EXTENSIONS = {
        '7z', 'avi', 'bmp', 'bz2', 'eot', 'exe', 'gif', 'gz', 'ico', 'jpeg',
        'jpg', 'mp3', 'mp4', 'otf', 'pdf', 'png', 'rar', 'tar', 'ttf', 'webm',
        'webp', 'woff', 'woff2', 'zip',
    }
    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/pdf',
        'application/zip',
        'application/gzip',
        'application/x-gzip',
        'application/x-zip-compressed',
        'image/',
        'audio/',
        'video/',
        'font/',
    )

    def __init__(self, request_callback, match_callback, progress_callback=None):
        """
        Initialize active shadow probing.

        :param callable request_callback: function used to fetch probe candidates
        :param callable match_callback: function called when a shadow copy is found
        :param callable|None progress_callback: optional progress callback
        """

        self.__request_callback = request_callback
        self.__match_callback = match_callback
        self.__progress_callback = progress_callback
        self.__suffixes = self.load_suffixes()
        self.__queue = Queue()
        self.__seen = set()
        self.__lock = threading.RLock()
        self.__submitted = 0
        self.__completed = 0
        self.__findings = 0
        self.__worker = threading.Thread(target=self.__run, name='opendoor-shadow-probe')
        self.__worker.daemon = True
        self.__worker.start()

    @property
    def submitted(self):
        """Return submitted shadow probe count."""

        with self.__lock:
            return int(self.__submitted)

    @property
    def completed(self):
        """Return completed shadow probe count."""

        with self.__lock:
            return int(self.__completed)

    @property
    def findings(self):
        """Return shadow finding count."""

        with self.__lock:
            return int(self.__findings)

    @classmethod
    def is_enabled(cls, config):
        """
        Return True when --sniff shadow is active.

        :param object config: browser config
        :return: whether active shadow probing should be enabled
        :rtype: bool
        """

        return getattr(config, 'is_sniff', False) is True and 'shadow' in (getattr(config, 'sniffers', []) or [])

    @classmethod
    def load_suffixes(cls):
        """
        Load unique suffixes from data/shadow-suffixes.dat.

        :return: normalized suffixes in stable file order
        :rtype: list[str]
        """

        path = CoreConfig.get('data').get('shadow_suffixes')
        suffixes = []
        seen = set()

        try:
            with open(path, 'r', encoding='utf-8') as handler:
                lines = handler.readlines()
        except (OSError, TypeError):
            lines = []

        for line in lines:
            suffix = str(line or '').strip()
            if not suffix or suffix in seen:
                continue
            suffixes.append(suffix)
            seen.add(suffix)

        return suffixes

    @classmethod
    def is_file_like_url(cls, url):
        """
        Decide whether a URL path can safely seed shadow postfix probes.

        :param str url: base URL
        :return: whether the URL points to a source/config-like file
        :rtype: bool
        """

        try:
            path = urlsplit(str(url)).path or ''
        except ValueError:
            return False

        if not path or path.endswith('/'):
            return False

        filename = path.rsplit('/', 1)[-1]
        lowered = filename.lower()

        if not filename or lowered in ('.', '..'):
            return False

        if lowered in cls.SPECIAL_FILENAMES:
            return True

        if '.' not in filename:
            return False

        extension = lowered.rsplit('.', 1)[-1]
        if extension in cls.BINARY_EXTENSIONS:
            return False

        return extension in cls.SOURCE_EXTENSIONS

    @classmethod
    def build_candidates(cls, url, suffixes):
        """
        Build postfix shadow candidates from one base URL.

        :param str url: base URL
        :param list[str] suffixes: configured suffixes
        :return: candidate URL and suffix pairs
        :rtype: list[tuple[str, str]]
        """

        try:
            parsed = urlsplit(str(url))
        except ValueError:
            return []

        path = parsed.path or ''
        if not path or path.endswith('/'):
            return []

        candidates = []
        for suffix in list(suffixes or [])[:cls.MAX_CANDIDATES_PER_HIT]:
            new_path = '{0}{1}'.format(path, suffix)
            candidates.append((urlunsplit((parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment)), suffix))

        return candidates

    @classmethod
    def response_signature(cls, response):
        """
        Build a compact normalized response body signature.

        :param object response: HTTP response-like object
        :return: signature metadata or None
        :rtype: dict|None
        """

        if cls.is_supported_response(response) is not True:
            return None

        data = getattr(response, 'data', b'')
        if data is None:
            return None

        if isinstance(data, bytes):
            raw = data[:cls.MAX_BODY_SIZE]
            text = helper.decode(raw, errors='ignore')
            size = len(data)
        else:
            text = str(data)[:cls.MAX_BODY_SIZE]
            size = len(str(data))

        normalized = cls.normalize_body(text)
        if not normalized:
            return None

        return {
            'hash': hashlib.sha256(normalized.encode('utf-8')).hexdigest(),
            'size': int(size),
            'content_type': cls.content_type(response),
        }

    @classmethod
    def normalize_body(cls, text):
        """
        Normalize body text for exact shadow-copy matching.

        :param str text: decoded body
        :return: normalized body
        :rtype: str
        """

        return str(text or '').replace('\r\n', '\n').replace('\r', '\n').strip()

    @classmethod
    def is_supported_response(cls, response):
        """
        Return True when response status/content-type can be compared.

        :param object response: HTTP response-like object
        :return: whether response is eligible
        :rtype: bool
        """

        try:
            if int(getattr(response, 'status', 0)) not in cls.SHADOW_STATUSES:
                return False
        except (TypeError, ValueError):
            return False

        content_type = cls.content_type(response)
        for binary_type in cls.BINARY_CONTENT_TYPES:
            if content_type.startswith(binary_type):
                return False

        return True

    @staticmethod
    def content_type(response):
        """
        Extract normalized Content-Type without parameters.

        :param object response: HTTP response-like object
        :return: normalized content type
        :rtype: str
        """

        headers = getattr(response, 'headers', {}) or {}
        value = ''

        try:
            value = headers.get('Content-Type') or headers.get('content-type') or ''
        except AttributeError:
            try:
                for key, item in dict(headers).items():
                    if str(key).lower() == 'content-type':
                        value = item
                        break
            except (TypeError, ValueError):
                value = ''

        return str(value or '').split(';', 1)[0].strip().lower()

    @classmethod
    def is_match(cls, base_signature, response):
        """
        Compare a shadow candidate response with its base signature.

        :param dict base_signature: base response signature
        :param object response: candidate response
        :return: candidate signature when matched, otherwise None
        :rtype: dict|None
        """

        candidate_signature = cls.response_signature(response)
        if not isinstance(base_signature, dict) or candidate_signature is None:
            return None

        if candidate_signature.get('hash') != base_signature.get('hash'):
            return None

        return candidate_signature

    @classmethod
    def build_metadata(cls, base_url, candidate_url, suffix, base_signature, candidate_signature):
        """
        Build report metadata for one confirmed shadow copy.

        :param str base_url: original 200 OK file URL
        :param str candidate_url: confirmed shadow copy URL
        :param str suffix: matched suffix
        :param dict base_signature: base response signature
        :param dict candidate_signature: candidate response signature
        :return: report metadata
        :rtype: dict
        """

        return {
            'shadow_detection': {
                'type': 'backup_copy',
                'confidence': 95,
                'reason': 'content_match',
                'base_url': str(base_url),
                'url': str(candidate_url),
                'variant': str(suffix),
                'variant_type': 'suffix',
                'similarity': 1.0,
                'base_size': int(base_signature.get('size', 0)),
                'shadow_size': int(candidate_signature.get('size', 0)),
                'content_type': str(candidate_signature.get('content_type', '')),
            }
        }

    def enqueue(self, base_url, base_response, bucket):
        """
        Queue active shadow probes for one successful base response.

        :param str base_url: base response URL
        :param object base_response: base response object
        :param str bucket: classified base bucket
        :return: queued candidate count
        :rtype: int
        """

        if bucket != 'success':
            return 0

        if self.is_file_like_url(base_url) is not True:
            return 0

        base_signature = self.response_signature(base_response)
        if base_signature is None:
            return 0

        queued = 0
        for candidate_url, suffix in self.build_candidates(base_url, self.__suffixes):
            with self.__lock:
                if self.__submitted >= self.MAX_TOTAL_PROBES:
                    break
                if candidate_url in self.__seen:
                    continue
                self.__seen.add(candidate_url)
                self.__submitted += 1
                current = self.__submitted

            self.__queue.put((base_url, base_signature, candidate_url, suffix, current))
            queued += 1

        return queued

    def drain(self):
        """
        Wait until all submitted shadow probes have completed.

        :return: None
        """

        self.__queue.join()

    def __run(self):
        """Run the bounded shadow probe worker loop."""

        while True:
            task = self.__queue.get(block=True)
            try:
                self.__process_task(task)
            finally:
                with self.__lock:
                    self.__completed += 1
                self.__queue.task_done()

    def __process_task(self, task):
        """
        Process one shadow probe candidate.

        :param tuple task: queued shadow probe task
        :return: None
        """

        base_url, base_signature, candidate_url, suffix, current = task

        try:
            candidate_response = self.__request_callback(candidate_url)
        except Exception:
            return

        candidate_signature = self.is_match(base_signature, candidate_response)
        if candidate_signature is None:
            if callable(self.__progress_callback):
                self.__progress_callback(candidate_url, candidate_response, current, self.submitted)
            return

        metadata = self.build_metadata(base_url, candidate_url, suffix, base_signature, candidate_signature)

        with self.__lock:
            self.__findings += 1

        if callable(self.__match_callback):
            self.__match_callback(candidate_url, candidate_response, metadata)
