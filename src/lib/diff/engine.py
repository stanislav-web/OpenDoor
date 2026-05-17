# -*- coding: utf-8 -*-

"""Compare normalized OpenDoor reports."""

from collections import defaultdict
from dataclasses import dataclass

from .records import DiffReport, DiffReportFinding


@dataclass(frozen=True)
class DiffFindingChange:
    """One finding that changed between two reports."""

    identity: tuple[str, str]
    previous: DiffReportFinding
    current: DiffReportFinding
    fields: dict


@dataclass(frozen=True)
class DiffResult:
    """Differential comparison result."""

    previous: DiffReport
    current: DiffReport
    added: tuple[DiffReportFinding, ...]
    removed: tuple[DiffReportFinding, ...]
    changed: tuple[DiffFindingChange, ...]
    unchanged_count: int

    @property
    def summary(self):
        """Return compact count summary for reports and stdout output."""

        return {
            'old_report': self.previous.path,
            'new_report': self.current.path,
            'added': len(self.added),
            'removed': len(self.removed),
            'changed': len(self.changed),
            'unchanged': self.unchanged_count,
        }


class DiffReportComparator(object):
    """Compare two normalized OpenDoor reports."""

    def compare(self, previous, current):
        """
        Compare previous and current report state.

        :param DiffReport previous: previous/baseline report
        :param DiffReport current: current report
        :return: DiffResult
        """

        previous_groups = group_findings(previous.findings)
        current_groups = group_findings(current.findings)

        added = []
        removed = []
        changed = []
        unchanged_count = 0

        identities = sorted(set(previous_groups) | set(current_groups))
        for identity in identities:
            old_group = previous_groups.get(identity, ())
            new_group = current_groups.get(identity, ())

            if not old_group:
                added.extend(new_group)
                continue

            if not new_group:
                removed.extend(old_group)
                continue

            group_result = compare_group(identity, old_group, new_group)
            added.extend(group_result.added)
            removed.extend(group_result.removed)
            changed.extend(group_result.changed)
            unchanged_count += group_result.unchanged_count

        return DiffResult(
            previous=previous,
            current=current,
            added=tuple(sorted(added, key=finding_sort_key)),
            removed=tuple(sorted(removed, key=finding_sort_key)),
            changed=tuple(sorted(changed, key=change_sort_key)),
            unchanged_count=unchanged_count,
        )


@dataclass(frozen=True)
class GroupDiffResult:
    """Internal comparison result for one endpoint identity."""

    added: tuple[DiffReportFinding, ...]
    removed: tuple[DiffReportFinding, ...]
    changed: tuple[DiffFindingChange, ...]
    unchanged_count: int


def group_findings(findings):
    """
    Group findings by stable endpoint identity.

    :param tuple[DiffReportFinding, ...] findings: normalized findings
    :return: dict[tuple[str, str], tuple[DiffReportFinding, ...]]
    """

    groups = defaultdict(list)
    for finding in findings:
        groups[finding.identity].append(finding)

    return {
        identity: tuple(sorted(values, key=finding_sort_key))
        for identity, values in groups.items()
    }


def compare_group(identity, previous_group, current_group):
    """
    Compare all findings for one endpoint identity.

    :param tuple[str, str] identity: method/url identity
    :param tuple[DiffReportFinding, ...] previous_group: previous findings
    :param tuple[DiffReportFinding, ...] current_group: current findings
    :return: GroupDiffResult
    """

    added = []
    removed = []
    changed = []
    unchanged_count = 0

    previous_by_bucket = map_by_bucket(previous_group)
    current_by_bucket = map_by_bucket(current_group)

    matched_previous = set()
    matched_current = set()

    for bucket in sorted(set(previous_by_bucket) & set(current_by_bucket)):
        previous_items = previous_by_bucket[bucket]
        current_items = current_by_bucket[bucket]
        pair_count = min(len(previous_items), len(current_items))

        for index in range(pair_count):
            previous_item = previous_items[index]
            current_item = current_items[index]
            matched_previous.add(id(previous_item))
            matched_current.add(id(current_item))

            fields = changed_fields(previous_item, current_item)
            if fields:
                changed.append(DiffFindingChange(
                    identity=identity,
                    previous=previous_item,
                    current=current_item,
                    fields=fields,
                ))
            else:
                unchanged_count += 1

    previous_leftovers = [item for item in previous_group if id(item) not in matched_previous]
    current_leftovers = [item for item in current_group if id(item) not in matched_current]

    if len(previous_leftovers) == 1 and len(current_leftovers) == 1:
        previous_item = previous_leftovers[0]
        current_item = current_leftovers[0]
        changed.append(DiffFindingChange(
            identity=identity,
            previous=previous_item,
            current=current_item,
            fields=changed_fields(previous_item, current_item),
        ))
    else:
        removed.extend(previous_leftovers)
        added.extend(current_leftovers)

    return GroupDiffResult(
        added=tuple(sorted(added, key=finding_sort_key)),
        removed=tuple(sorted(removed, key=finding_sort_key)),
        changed=tuple(sorted(changed, key=change_sort_key)),
        unchanged_count=unchanged_count,
    )


def map_by_bucket(findings):
    """
    Group one endpoint's findings by bucket.

    :param tuple[DiffReportFinding, ...] findings: findings with the same identity
    :return: dict[str, tuple[DiffReportFinding, ...]]
    """

    buckets = defaultdict(list)
    for finding in findings:
        buckets[finding.bucket].append(finding)

    return {
        bucket: tuple(sorted(values, key=finding_sort_key))
        for bucket, values in buckets.items()
    }


def changed_fields(previous, current):
    """
    Return changed comparable fields.

    :param DiffReportFinding previous: old finding
    :param DiffReportFinding current: new finding
    :return: dict[str, tuple[str, str]]
    """

    fields = {}
    previous_data = previous.comparable
    current_data = current.comparable

    for field in sorted(set(previous_data) | set(current_data)):
        previous_value = previous_data.get(field, '')
        current_value = current_data.get(field, '')
        if previous_value != current_value:
            fields[field] = (previous_value, current_value)

    return fields


def finding_sort_key(finding):
    """
    Return deterministic finding sort key.

    :param DiffReportFinding finding: finding
    :return: tuple[str, str, str, str, str, str]
    """

    return (
        finding.url,
        finding.method,
        finding.bucket,
        finding.status,
        finding.size,
        finding.location,
    )


def change_sort_key(change):
    """
    Return deterministic changed-finding sort key.

    :param DiffFindingChange change: changed finding
    :return: tuple[str, str, str, str, str, str]
    """

    return finding_sort_key(change.current)
