# -*- coding: utf-8 -*-

"""Shared sniffer response context primitives."""


class SnifferContext:
    """Immutable response context shared by sniffer engines."""

    __slots__ = (
        'base_status',
        'body',
        'code',
        'headers',
        'metadata',
        'request_url',
        'response',
        'size',
    )

    def __init__(self, request_url, response=None, base_status=None, code=None, size=None,
                 body='', headers=None, metadata=None):
        """
        Create a sniffer context.

        :param str request_url: original request URL
        :param object response: raw HTTP response object
        :param str | None base_status: base OpenDoor response bucket
        :param str | int | None code: HTTP status code
        :param str | int | None size: normalized response size
        :param str | bytes | None body: decoded response body
        :param dict | None headers: response headers
        :param dict | None metadata: extra context metadata
        """

        self.request_url = request_url
        self.response = response
        self.base_status = base_status
        self.code = None if code is None else str(code)
        self.size = None if size is None else str(size)
        self.body = '' if body is None else body
        self.headers = dict(headers or {})
        self.metadata = dict(metadata or {})

    def with_metadata(self, **metadata):
        """
        Return a copy of the context with merged metadata.

        :param dict metadata: metadata values to merge
        :return: SnifferContext
        """

        merged_metadata = dict(self.metadata)
        merged_metadata.update(metadata)

        return SnifferContext(
            request_url=self.request_url,
            response=self.response,
            base_status=self.base_status,
            code=self.code,
            size=self.size,
            body=self.body,
            headers=self.headers,
            metadata=merged_metadata,
        )
