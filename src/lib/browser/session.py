# -*- coding: utf-8 -*-

"""
    Persistent browser session checkpoints.

    This module stores only logical scan state:
    - filtered params
    - resolved targets
    - pending queue
    - completed/seen queue
    - recursive state
    - partial result
    - fingerprint result

    It does NOT try to serialize live threads, sockets or responses.
"""

import copy
import hashlib
import json
import os
import shutil
import tempfile
import time


class SessionError(Exception):
    """SessionError class"""

    def __init__(self, message):
        """
        SessionError class constructor
        :param str message: error message
        """

        super(SessionError, self).__init__(message)


class SessionManager(object):
    """SessionManager class"""

    SCHEMA_VERSION = 1
    DEFAULT_AUTOSAVE_SEC = 20
    DEFAULT_AUTOSAVE_ITEMS = 200

    def __init__(self, path, autosave_sec=None, autosave_items=None):
        """
        Init session manager.

        :param str path:
        :param int autosave_sec:
        :param int autosave_items:
        """

        self._path = path
        self._backup_path = str(path) + '.bak'
        self._autosave_sec = self.DEFAULT_AUTOSAVE_SEC if autosave_sec is None else int(autosave_sec)
        self._autosave_items = self.DEFAULT_AUTOSAVE_ITEMS if autosave_items is None else int(autosave_items)
        self._last_saved_at = 0.0
        self._last_saved_processed = 0

    @property
    def path(self):
        """Session file path."""
        return self._path

    @property
    def backup_path(self):
        """Backup session file path."""
        return self._backup_path

    @property
    def autosave_sec(self):
        """Autosave seconds threshold."""
        return self._autosave_sec

    @property
    def autosave_items(self):
        """Autosave processed-items threshold."""
        return self._autosave_items

    @classmethod
    def app_version(cls):
        """
        Read project version from VERSION file.

        :return: str
        """

        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        version_path = os.path.join(root, 'VERSION')

        try:
            with open(version_path, 'r', encoding='utf-8') as handle:
                return handle.read().strip()
        except OSError:
            return 'unknown'

    @classmethod
    def now(cls):
        """
        Current unix timestamp.

        :return: int
        """

        return int(time.time())

    @classmethod
    def _serialize_checksum_payload(cls, payload):
        """
        Serialize payload for checksum generation.

        :param dict payload:
        :return: str
        """

        return json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

    @classmethod
    def build_checksum(cls, snapshot):
        """
        Build checksum for snapshot.

        :param dict snapshot:
        :return: str
        """

        payload = copy.deepcopy(snapshot)
        payload.pop('checksum', None)
        digest = hashlib.sha256(cls._serialize_checksum_payload(payload).encode('utf-8'))
        return digest.hexdigest()

    @classmethod
    def validate_task_list(cls, tasks, key):
        """
        Validate session task list.

        :param list tasks:
        :param str key:
        :raise SessionError:
        :return: list[dict]
        """

        if not isinstance(tasks, list):
            raise SessionError('{0} must be a list'.format(key))

        normalized = []
        for item in tasks:
            if not isinstance(item, dict):
                raise SessionError('{0} items must be objects'.format(key))

            url = item.get('url')
            depth = item.get('depth')

            if not isinstance(url, str) or not url.strip():
                raise SessionError('{0} item url must be a non-empty string'.format(key))

            try:
                depth = int(depth)
            except (TypeError, ValueError):
                raise SessionError('{0} item depth must be an integer'.format(key))

            if depth < 0:
                raise SessionError('{0} item depth must be non-negative'.format(key))

            normalized.append({'url': url, 'depth': depth})

        return normalized

    @classmethod
    def validate_string_list(cls, values, key):
        """
        Validate list[str] style fields.

        :param list values:
        :param str key:
        :raise SessionError:
        :return: list[str]
        """

        if not isinstance(values, list):
            raise SessionError('{0} must be a list'.format(key))

        normalized = []
        for item in values:
            if not isinstance(item, str):
                raise SessionError('{0} items must be strings'.format(key))
            if item.strip():
                normalized.append(item)

        return normalized

    @classmethod
    def validate_snapshot(cls, snapshot):
        """
        Validate loaded snapshot.

        :param dict snapshot:
        :raise SessionError:
        :return: dict
        """

        if not isinstance(snapshot, dict):
            raise SessionError('Session snapshot must be a JSON object')

        required = [
            'schemaVersion',
            'appVersion',
            'createdAt',
            'updatedAt',
            'params',
            'targets',
            'pending',
            'seen',
            'queuedRecursive',
            'visitedRecursive',
            'result',
            'stats',
            'checksum',
        ]

        for key in required:
            if key not in snapshot:
                raise SessionError('Missing required session field `{0}`'.format(key))

        if int(snapshot.get('schemaVersion')) != cls.SCHEMA_VERSION:
            raise SessionError(
                'Unsupported session schema version `{0}`'.format(snapshot.get('schemaVersion'))
            )

        if not isinstance(snapshot.get('params'), dict):
            raise SessionError('Session field `params` must be an object')

        if not isinstance(snapshot.get('targets'), list):
            raise SessionError('Session field `targets` must be a list')

        cls.validate_task_list(snapshot.get('pending'), 'pending')
        cls.validate_string_list(snapshot.get('seen'), 'seen')
        cls.validate_string_list(snapshot.get('queuedRecursive'), 'queuedRecursive')
        cls.validate_string_list(snapshot.get('visitedRecursive'), 'visitedRecursive')

        if not isinstance(snapshot.get('result'), dict):
            raise SessionError('Session field `result` must be an object')

        if not isinstance(snapshot.get('stats'), dict):
            raise SessionError('Session field `stats` must be an object')

        processed = snapshot.get('stats', {}).get('processed', 0)
        total_items = snapshot.get('stats', {}).get('total_items', 0)

        try:
            processed = int(processed)
            total_items = int(total_items)
        except (TypeError, ValueError):
            raise SessionError('Session stats counters must be integers')

        if processed < 0 or total_items < 0:
            raise SessionError('Session stats counters must be non-negative')

        actual_checksum = cls.build_checksum(snapshot)
        if actual_checksum != snapshot.get('checksum'):
            raise SessionError('Session checksum mismatch')

        return snapshot

    @classmethod
    def _load_single(cls, path):
        """
        Load and validate a single session file.

        :param str path:
        :raise SessionError:
        :return: dict
        """

        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)

        return cls.validate_snapshot(data)

    @classmethod
    def load(cls, path):
        """
        Load session snapshot. Fallback to .bak if main file is invalid.

        :param str path:
        :raise SessionError:
        :return: dict
        """

        errors = []

        for candidate in [path, str(path) + '.bak']:
            try:
                if os.path.exists(candidate):
                    snapshot = cls._load_single(candidate)
                    snapshot['_loaded_from'] = candidate
                    return snapshot
            except (OSError, ValueError, SessionError) as error:
                errors.append('{0}: {1}'.format(candidate, error))

        if errors:
            raise SessionError('Unable to load a valid session snapshot. ' + ' | '.join(errors))

        raise SessionError('Session file `{0}` does not exist'.format(path))

    def should_save(self, dirty, processed, force=False):
        """
        Decide whether session checkpoint should be written.

        :param bool dirty:
        :param int processed:
        :param bool force:
        :return: bool
        """

        if force is True:
            return True

        if True is not dirty:
            return False

        now = time.time()
        if (now - self._last_saved_at) >= self._autosave_sec:
            return True

        if (int(processed) - int(self._last_saved_processed)) >= self._autosave_items:
            return True

        return False

    def save(self, snapshot):
        """
        Save session snapshot atomically and maintain .bak backup.

        :param dict snapshot:
        :raise SessionError:
        :return: None
        """

        directory = os.path.dirname(os.path.abspath(self._path)) or '.'
        if not os.path.isdir(directory):
            os.makedirs(directory)

        payload = copy.deepcopy(snapshot)
        payload['schemaVersion'] = self.SCHEMA_VERSION
        payload['appVersion'] = self.app_version()
        payload['updatedAt'] = self.now()
        payload['checksum'] = self.build_checksum(payload)

        self.validate_snapshot(payload)

        if os.path.exists(self._path):
            try:
                shutil.copyfile(self._path, self._backup_path)
            except OSError:
                pass

        fd, tmp_path = tempfile.mkstemp(prefix='opendoor-session-', suffix='.tmp', dir=directory)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(tmp_path, self._path)
        except OSError as error:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except OSError:
                pass
            raise SessionError('Unable to save session file `{0}`. {1}'.format(self._path, error))

        self._last_saved_at = time.time()
        self._last_saved_processed = int(payload.get('stats', {}).get('processed', 0))