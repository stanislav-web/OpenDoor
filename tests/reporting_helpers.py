# -*- coding: utf-8 -*-

"""Shared helpers for report plugin tests."""

import csv
import json
import os
import sqlite3


def report_file_path(base_dir, target, extension):
    """
    Build a target-scoped report file path.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :param extension: Report file extension without a leading dot.
    :return: Absolute report file path.
    """

    return os.path.join(base_dir, target, f'{target}.{extension}')


def bucket_file_path(base_dir, target, bucket):
    """
    Build a target-scoped bucket report file path.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :param bucket: Report bucket filename without extension.
    :return: Absolute bucket report file path.
    """

    return os.path.join(base_dir, target, f'{bucket}.txt')


def read_csv_report(base_dir, target):
    """
    Read a CSV report into dictionaries.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :return: CSV report rows as dictionaries.
    """

    with open(report_file_path(base_dir, target, 'csv'), newline='', encoding='utf-8') as handler:
        return list(csv.DictReader(handler))


def read_json_report(base_dir, target):
    """
    Read a JSON report payload.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :return: Parsed JSON report payload.
    """

    with open(report_file_path(base_dir, target, 'json'), encoding='utf-8') as handler:
        return json.load(handler)


def fetch_sqlite_row(base_dir, target, query):
    """
    Execute a SQLite query and fetch the first row.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :param query: SQL query to execute.
    :return: First SQLite row for the query.
    """

    connection = sqlite3.connect(report_file_path(base_dir, target, 'sqlite'))
    try:
        return connection.execute(query).fetchone()
    finally:
        connection.close()


def fetch_sqlite_row_and_summary(base_dir, target, query):
    """
    Execute a SQLite item query and read summary totals.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :param query: SQL query to execute against report items.
    :return: Tuple with first row and summary totals dictionary.
    """

    connection = sqlite3.connect(report_file_path(base_dir, target, 'sqlite'))
    try:
        row = connection.execute(query).fetchone()
        summary = dict(connection.execute('SELECT status, total FROM summary').fetchall())
        return row, summary
    finally:
        connection.close()


def read_bucket_report(base_dir, target, bucket):
    """
    Read a text bucket report.

    :param base_dir: Base temporary report directory.
    :param target: Report target name.
    :param bucket: Report bucket filename without extension.
    :return: Text bucket report content.
    """

    with open(bucket_file_path(base_dir, target, bucket), encoding='utf-8') as handler:
        return handler.read()
