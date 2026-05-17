# -*- coding: utf-8 -*-

"""Output helpers for differential report comparison."""


class DiffResultSerializer(object):
    """Serialize DiffResult into deterministic JSON-compatible structures."""

    def serialize(self, result):
        """
        Serialize a diff result.

        :param DiffResult result: comparison result
        :return: dict
        """

        return {
            'summary': result.summary,
            'added': [serialize_finding(finding) for finding in result.added],
            'removed': [serialize_finding(finding) for finding in result.removed],
            'changed': [serialize_change(change) for change in result.changed],
        }


class DiffStdoutFormatter(object):
    """Format DiffResult as a readable stdout report."""

    def format(self, result):
        """
        Format a diff result for terminal output.

        :param DiffResult result: comparison result
        :return: str
        """

        lines = []
        lines.extend(self._summary_lines(result))
        lines.append('')
        lines.extend(self._finding_section('Added', result.added))
        lines.append('')
        lines.extend(self._finding_section('Removed', result.removed))
        lines.append('')
        lines.extend(self._changed_section(result.changed))
        return '\n'.join(lines).rstrip() + '\n'

    @staticmethod
    def _summary_lines(result):
        summary = result.summary
        return [
            'Differential scan summary',
            'old_report: {0}'.format(summary['old_report']),
            'new_report: {0}'.format(summary['new_report']),
            'added: {0}'.format(summary['added']),
            'removed: {0}'.format(summary['removed']),
            'changed: {0}'.format(summary['changed']),
            'unchanged: {0}'.format(summary['unchanged']),
        ]

    @staticmethod
    def _finding_section(title, findings):
        lines = ['{0}:'.format(title)]
        if not findings:
            lines.append('  -')
            return lines

        for finding in findings:
            lines.append('  {0}'.format(format_finding_line(finding)))

        return lines

    @staticmethod
    def _changed_section(changes):
        lines = ['Changed:']
        if not changes:
            lines.append('  -')
            return lines

        for change in changes:
            lines.append('  {0}'.format(format_finding_line(change.current)))
            for field in sorted(change.fields):
                previous, current = change.fields[field]
                lines.append('    {0}: {1} -> {2}'.format(
                    field,
                    printable_value(previous),
                    printable_value(current),
                ))

        return lines


def serialize_finding(finding):
    """
    Serialize one normalized diff finding.

    :param DiffReportFinding finding: finding
    :return: dict
    """

    return {
        'bucket': finding.bucket,
        'url': finding.url,
        'method': finding.method,
        'status': finding.status,
        'size': finding.size,
        'location': finding.location,
    }


def serialize_change(change):
    """
    Serialize one changed finding.

    :param DiffFindingChange change: changed finding
    :return: dict
    """

    return {
        'identity': {
            'method': change.identity[0],
            'url': change.identity[1],
        },
        'previous': serialize_finding(change.previous),
        'current': serialize_finding(change.current),
        'fields': {
            field: {
                'previous': values[0],
                'current': values[1],
            }
            for field, values in sorted(change.fields.items())
        },
    }


def format_finding_line(finding):
    """
    Format one finding for stdout.

    :param DiffReportFinding finding: finding
    :return: str
    """

    parts = [
        '[{0}]'.format(finding.bucket),
        printable_value(finding.status),
        printable_value(finding.size),
    ]

    if finding.method:
        parts.append(finding.method)

    parts.append(finding.url)

    if finding.location:
        parts.append('-> {0}'.format(finding.location))

    return ' '.join(parts)


def printable_value(value):
    """
    Return terminal-friendly value placeholder.

    :param object value: value
    :return: str
    """

    if value is None or value == '':
        return '-'

    return str(value)
