# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development: Stanislav WEB
"""

import json
import os
from xml.sax.saxutils import escape as xml_escape

from .provider import PluginProvider
from src.core import CoreConfig
from src.core import filesystem, FileSystemError


class HtmlReportPlugin(PluginProvider):
    """ HtmlReportPlugin class"""

    PLUGIN_NAME = 'HtmlReport'
    EXTENSION_SET = '.html'

    def __init__(self, target, data, directory=None):
        """
        PluginProvider constructor
        :param str target: target host
        :param dict data: result set
        :param str directory: custom directory
        """

        PluginProvider.__init__(self, target, data)

        try:

            if None is directory:
                directory = CoreConfig.get('data').get('reports')
            self.__target_dir = filesystem.makedir(os.path.join(directory, self._target))
        except FileSystemError as error:
            raise Exception(error)

    def process(self):
        """
        Process data
        :return: str
        """

        try:
            filesystem.clear(self.__target_dir, extension=self.EXTENSION_SET)
            report_data = dict(self._data)
            report_data['report_items'] = {
                status: self.get_report_items(status)
                for status in self._data.get('items', {}).keys()
            }
            resultset = render_html_report(self._target, report_data)
            self.record(self.__target_dir, self._target, resultset)
        except FileSystemError as error:
            raise Exception(error)


def render_html_report(target, report_data):
    """
    Render OpenDoor report data as a standalone HTML document.

    :param str target: target host
    :param dict report_data: report payload
    :return: HTML document
    :rtype: str
    """

    target = _escape(target)
    totals = report_data.get('total', {})
    report_items = report_data.get('report_items', {})
    metadata = _get_metadata(report_data)

    return ''.join([
        '<!doctype html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>OpenDoor Report - {0}</title>'.format(target),
        '<style>',
        _get_report_css(),
        '</style>',
        '</head>',
        '<body>',
        '<main class="page">',
        '<section class="hero">',
        '<div>',
        '<p class="eyebrow">OpenDoor Report</p>',
        '<h1>{0}</h1>'.format(target),
        '<p class="subtitle">Authorized web reconnaissance and directory discovery results.</p>',
        '</div>',
        '<div class="hero-badge">HTML</div>',
        '</section>',
        _render_report_nav(report_items, metadata),
        _render_totals(totals),
        _render_report_items(report_items),
        _render_metadata(metadata),
        '</main>',
        _get_report_js(),
        '</body>',
        '</html>',
    ])


def _get_report_css():
    """
    Return embedded report stylesheet.

    :return: CSS stylesheet
    :rtype: str
    """

    return """
:root {
  color-scheme: light;
  --bg: #f4f7fb;
  --panel: #ffffff;
  --panel-soft: #f8fafc;
  --text: #111827;
  --muted: #6b7280;
  --border: #e5e7eb;
  --border-strong: #cbd5e1;
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --success: #047857;
  --success-soft: #ecfdf5;
  --warning: #b45309;
  --warning-soft: #fffbeb;
  --danger: #b91c1c;
  --danger-soft: #fef2f2;
  --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
}

button,
input {
  font: inherit;
}

.page {
  width: min(1240px, calc(100% - 32px));
  margin: 32px auto;
}

.hero,
.section,
.report-nav {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.15;
}

h2 {
  margin: 0;
  font-size: 18px;
}

h3 {
  margin: 0;
  font-size: 15px;
}

.subtitle {
  margin: 8px 0 0;
  color: var(--muted);
}

.hero-badge {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 700;
}

.report-nav {
  position: sticky;
  top: 12px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px;
  margin-bottom: 18px;
}

.report-nav-links,
.report-actions,
.status-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.report-nav a,
.status-tab,
.action-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 7px 11px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #fff;
  color: var(--text);
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}

.report-nav a:hover,
.status-tab:hover,
.action-button:hover {
  border-color: var(--border-strong);
  background: var(--panel-soft);
  text-decoration: none;
}

.action-button,
.status-tab {
  appearance: none;
}

.action-button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.copy-feedback {
  align-self: center;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.status-tab.is-active,
.status-tab[aria-selected="true"] {
  border-color: #bfdbfe;
  background: var(--accent-soft);
  color: var(--accent);
}

.section {
  margin-top: 18px;
  overflow: hidden;
  scroll-margin-top: 86px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--panel-soft);
}

.section-description {
  margin: 4px 0 0;
  color: var(--muted);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  padding: 18px 20px 20px;
}

.card {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #fff;
}

.card-label {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-value {
  margin: 0;
  font-size: 24px;
  font-weight: 750;
}

.finding-controls {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: #fff;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  color: var(--muted);
  font-weight: 700;
}

.search-box input {
  width: 100%;
  min-height: 38px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  color: var(--text);
  outline: none;
}

.search-box input:focus {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.status-block {
  padding: 18px 20px 20px;
  border-top: 1px solid var(--border);
  scroll-margin-top: 110px;
}

.status-block:first-of-type {
  border-top: 0;
}

.status-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 14px;
}

table {
  width: 100%;
  min-width: 760px;
  border-collapse: separate;
  border-spacing: 0;
  background: #fff;
}

.report-table {
  table-layout: fixed;
}

th,
td {
  padding: 11px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  text-align: left;
}

th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f3f4f6;
  color: #374151;
  font-size: 12px;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  overflow-wrap: anywhere;
  word-break: break-word;
}

tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover td {
  background: #f9fafb;
}

a {
  color: var(--accent);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}

.break {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.badge {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.badge-success {
  background: var(--success-soft);
  color: var(--success);
}

.badge-warning {
  background: var(--warning-soft);
  color: var(--warning);
}

.badge-danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.empty {
  margin: 0;
  padding: 18px 20px;
  color: var(--muted);
}

.search-empty {
  margin: 0;
  padding: 0 20px 18px;
  color: var(--muted);
  font-weight: 700;
}

.value-list {
  margin: 0;
  padding-left: 18px;
}

.value-list li {
  margin: 3px 0;
}

.nested {
  margin: 0;
  padding: 10px;
  border-radius: 10px;
  background: #f9fafb;
  border: 1px solid var(--border);
  white-space: pre-wrap;
}

.details-block {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.details-block summary {
  padding: 9px 11px;
  background: var(--panel-soft);
  color: var(--text);
  font-weight: 700;
  cursor: pointer;
}

.details-block .nested {
  border: 0;
  border-top: 1px solid var(--border);
  border-radius: 0;
}

.is-hidden,
[hidden] {
  display: none !important;
}

@media (max-width: 760px) {
  .page {
    width: min(100% - 20px, 1240px);
    margin: 16px auto;
  }

  .hero,
  .section-header,
  .report-nav,
  .finding-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .finding-controls {
    display: flex;
  }

  .status-tabs,
  .report-actions,
  .report-nav-links {
    width: 100%;
  }

  .status-tab,
  .action-button,
  .report-nav a {
    justify-content: center;
  }
}

@media print {
  body {
    background: #fff;
  }

  .page {
    width: 100%;
    margin: 0;
  }

  .hero,
  .section,
  .report-nav {
    box-shadow: none;
  }

  .report-nav,
  .finding-controls,
  .action-button {
    display: none;
  }

  th {
    position: static;
  }
}
"""


def _get_report_js():
    """
    Return embedded report script.

    The script is intentionally dependency-free so HTML reports remain fully standalone.

    :return: JavaScript source
    :rtype: str
    """

    return """
<script>
(function () {
  var findings = document.querySelector('[data-report-findings]');

  if (!findings) {
    return;
  }

  var searchInput = findings.querySelector('[data-report-search]');
  var statusButtons = Array.prototype.slice.call(findings.querySelectorAll('[data-status-filter]'));
  var copyButton = document.querySelector('[data-copy-visible-urls]');
  var copyStatus = document.querySelector('[data-copy-status]');
  var emptyMessage = findings.querySelector('[data-search-empty]');
  var activeStatus = 'all';
  var hasRowLevelFilter = false;

  function normalize(value) {
    return String(value || '').toLowerCase().replace(/\\s+/g, ' ').trim();
  }

  function getGroups() {
    return Array.prototype.slice.call(findings.querySelectorAll('[data-report-status]'));
  }

  function getRows() {
    return Array.prototype.slice.call(findings.querySelectorAll('[data-report-row]'));
  }

  function isVisibleRow(row) {
    var group = row.closest('[data-report-status]');
    return row && group && !row.hidden && !group.hidden;
  }

  function getRowUrl(row) {
    var explicit = row.getAttribute('data-report-url');

    if (explicit) {
      return explicit;
    }

    var anchor = row.querySelector('a[href^="http"]');
    return anchor ? anchor.getAttribute('href') : '';
  }

  function getVisibleUrls() {
    var seen = {};
    var urls = [];

    getRows().forEach(function (row) {
      var url = isVisibleRow(row) ? getRowUrl(row) : '';

      if (url && !seen[url]) {
        seen[url] = true;
        urls.push(url);
      }
    });

    return urls;
  }

  function setCopyStatus(message) {
    if (copyStatus) {
      copyStatus.textContent = message || '';
    }
  }

  function updateCopyButton() {
    if (!copyButton) {
      return;
    }

    var count = getVisibleUrls().length;
    copyButton.disabled = count === 0;
    copyButton.textContent = count ? 'Copy visible URLs (' + count + ')' : 'No visible URLs';
  }

  function updateEmptyMessage(visibleRows) {
    if (!emptyMessage) {
      return;
    }

    emptyMessage.hidden = visibleRows !== 0;
  }

  function getRowSearchText(row) {
    return normalize(row.getAttribute('data-row-search') || row.innerText || row.textContent);
  }

  function getGroupCount(group) {
    var explicit = parseInt(group.getAttribute('data-report-count') || '0', 10);

    if (!isNaN(explicit)) {
      return explicit;
    }

    return group.querySelectorAll('[data-report-row]').length;
  }

  function getActiveTarget() {
    return activeStatus === 'all'
      ? findings
      : findings.querySelector('[data-report-status="' + activeStatus.replace(/"/g, '\\"') + '"]');
  }

  function updateLocationHash(target) {
    if (!target || !target.id) {
      return;
    }

    try {
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', '#' + target.id);
        return;
      }
    } catch (error) {
      // Fall back to location.hash for browsers that restrict file:// history updates.
    }

    window.location.hash = target.id;
  }

  function scrollToActiveGroup() {
    var target = getActiveTarget();

    updateLocationHash(target);

    if (!target || !target.scrollIntoView) {
      return;
    }

    try {
      target.scrollIntoView({ block: 'start', behavior: 'smooth' });
    } catch (error) {
      target.scrollIntoView(true);
    }
  }

  function applyFilters() {
    var query = normalize(searchInput ? searchInput.value : '');
    var visibleTotal = 0;
    var shouldTouchRows = !!query || hasRowLevelFilter;

    getGroups().forEach(function (group) {
      var status = group.getAttribute('data-report-status');
      var statusMatches = activeStatus === 'all' || status === activeStatus;
      var rows;
      var visibleRows = 0;

      if (!statusMatches) {
        group.hidden = true;
        return;
      }

      if (!shouldTouchRows) {
        group.hidden = false;
        visibleTotal += getGroupCount(group);
        return;
      }

      rows = Array.prototype.slice.call(group.querySelectorAll('[data-report-row]'));

      rows.forEach(function (row) {
        var rowMatches = !query || getRowSearchText(row).indexOf(query) !== -1;
        row.hidden = !rowMatches;

        if (rowMatches) {
          visibleRows += 1;
          visibleTotal += 1;
        }
      });

      group.hidden = rows.length > 0 && visibleRows === 0;
    });

    hasRowLevelFilter = !!query;
    updateEmptyMessage(visibleTotal);
    updateCopyButton();
    setCopyStatus('');
  }

  statusButtons.forEach(function (button) {
    button.addEventListener('click', function (event) {
      if (event && event.preventDefault) {
        event.preventDefault();
      }

      activeStatus = button.getAttribute('data-status-filter') || 'all';

      statusButtons.forEach(function (item) {
        var selected = item === button;
        item.classList.toggle('is-active', selected);
        item.setAttribute('aria-selected', selected ? 'true' : 'false');
      });

      applyFilters();
      scrollToActiveGroup();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  if (copyButton) {
    copyButton.addEventListener('click', function () {
      var urls = getVisibleUrls();
      var payload = urls.join('\n');

      if (!urls.length) {
        setCopyStatus('No visible URLs to copy.');
        return;
      }

      function markCopied() {
        updateCopyButton();
        setCopyStatus('Copied ' + urls.length + ' URL' + (urls.length === 1 ? '' : 's') + '.');
      }

      function markFailed() {
        setCopyStatus('Copy failed. Select and copy the visible URLs manually.');
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(payload).then(markCopied, function () {
          fallbackCopy(payload, markCopied, markFailed);
        });
        return;
      }

      fallbackCopy(payload, markCopied, markFailed);
    });
  }

  function fallbackCopy(payload, onSuccess, onFailure) {
    var buffer = document.createElement('textarea');
    var copied = false;

    buffer.value = payload;
    buffer.setAttribute('readonly', 'readonly');
    buffer.style.position = 'fixed';
    buffer.style.left = '-9999px';
    buffer.style.top = '0';
    document.body.appendChild(buffer);
    buffer.focus();
    buffer.select();

    try {
      copied = document.execCommand && document.execCommand('copy');
    } catch (error) {
      copied = false;
    }

    document.body.removeChild(buffer);

    if (copied) {
      onSuccess();
      return;
    }

    onFailure();
  }

  applyFilters();
}());
</script>
"""


def _render_report_nav(report_items, metadata):
    """
    Render sticky in-page report navigation.

    :param dict report_items: status-to-items map
    :param dict metadata: metadata map
    :return: HTML fragment
    :rtype: str
    """

    links = [
        '<a href="#summary">Summary</a>',
        '<a href="#findings">Findings <span class="badge">{0}</span></a>'.format(
            _escape(_get_total_finding_count(report_items)),
        ),
    ]

    if metadata:
        links.append('<a href="#metadata">Metadata</a>')

    return (
        '<nav class="report-nav" aria-label="Report navigation">'
        '<div class="report-nav-links">{0}</div>'
        '<div class="report-actions">'
        '<button class="action-button" type="button" data-copy-visible-urls>Copy visible URLs</button>'
        '<span class="copy-feedback" data-copy-status aria-live="polite"></span>'
        '</div>'
        '</nav>'
    ).format(''.join(links))


def _get_total_finding_count(report_items):
    """
    Return total number of rendered findings.

    :param dict report_items: status-to-items map
    :return: total item count
    :rtype: int
    """

    if not isinstance(report_items, dict):
        return 0

    count = 0

    for items in report_items.values():
        if isinstance(items, list):
            count += len(items)

    return count


def _render_status_filter_buttons(report_items):
    """
    Render finding status filter buttons.

    :param dict report_items: status-to-items map
    :return: HTML fragment
    :rtype: str
    """

    total_count = _get_total_finding_count(report_items)
    buttons = [
        '<a class="status-tab is-active" href="#findings" data-status-filter="all" '
        'role="tab" aria-selected="true" aria-controls="findings">'
        'All <span class="badge">{0}</span></a>'.format(
            _escape(total_count),
        )
    ]

    for status in sorted(report_items.keys()):
        items = report_items.get(status) or []
        count = len(items) if isinstance(items, list) else 0
        buttons.append(
            '<a class="status-tab" href="#{1}" data-status-filter="{0}" '
            'role="tab" aria-selected="false" aria-controls="{1}">'
            '{2} <span class="{3}">{4}</span></a>'.format(
                _escape(status),
                _get_status_dom_id(status),
                _escape(status),
                _get_status_badge_class(status),
                _escape(count),
            )
        )

    return ''.join(buttons)


def _render_totals(totals):
    """
    Render total statistics block.

    :param dict totals: total counters
    :return: HTML fragment
    :rtype: str
    """

    if not isinstance(totals, dict) or not totals:
        return ''

    cards = []

    for key in _get_ordered_total_keys(totals):
        cards.append(
            '<article class="card">'
            '<p class="card-label">{0}</p>'
            '<p class="card-value">{1}</p>'
            '</article>'.format(
                _escape(key),
                _escape(totals.get(key)),
            )
        )

    return (
        '<section class="section" id="summary">'
        '<div class="section-header">'
        '<div>'
        '<h2>Summary</h2>'
        '<p class="section-description">Aggregated scan counters.</p>'
        '</div>'
        '</div>'
        '<div class="cards">{0}</div>'
        '</section>'
    ).format(''.join(cards))


def _get_ordered_total_keys(totals):
    """
    Return stable total-card order with known scan counters first.

    :param dict totals: total counters
    :return: ordered total keys
    :rtype: list
    """

    preferred = [
        'items',
        'success',
        'auth',
        'forbidden',
        'blocked',
        'bypass',
        'redirect',
        'failed',
        'workers',
    ]
    existing = list(totals.keys())
    ordered = [key for key in preferred if key in totals]
    ordered.extend(sorted(key for key in existing if key not in ordered))

    return ordered


def _render_report_items(report_items):
    """
    Render discovered report items grouped by status.

    :param dict report_items: status-to-items map
    :return: HTML fragment
    :rtype: str
    """

    if not isinstance(report_items, dict) or not report_items:
        return (
            '<section class="section" id="findings">'
            '<div class="section-header">'
            '<div>'
            '<h2>Findings</h2>'
            '<p class="section-description">No report items were generated.</p>'
            '</div>'
            '</div>'
            '<p class="empty">No findings.</p>'
            '</section>'
        )

    sections = []

    for status in sorted(report_items.keys()):
        items = report_items.get(status) or []
        sections.append(_render_status_items(status, items))

    return (
        '<section class="section" id="findings" data-report-findings>'
        '<div class="section-header">'
        '<div>'
        '<h2>Findings</h2>'
        '<p class="section-description">Discovered resources grouped by OpenDoor status.</p>'
        '</div>'
        '</div>'
        '<div class="finding-controls">'
        '<label class="search-box">Search '
        '<input type="search" data-report-search placeholder="Filter by URL, code, WAF, title, header...">'
        '</label>'
        '<div class="status-tabs" role="tablist" aria-label="Finding status filters">{0}</div>'
        '</div>'
        '<p class="search-empty" data-search-empty hidden>No findings match the current filters.</p>'
        '{1}'
        '</section>'
    ).format(
        _render_status_filter_buttons(report_items),
        ''.join(sections),
    )


def _render_status_items(status, items):
    """
    Render one status group.

    :param str status: item status
    :param list items: status items
    :return: HTML fragment
    :rtype: str
    """

    count = len(items) if isinstance(items, list) else 0

    if not items:
        table = '<p class="empty">No items in this bucket.</p>'
    elif all(isinstance(item, dict) for item in items):
        table = _render_list_of_dicts(items)
    else:
        table = _render_plain_list(items)

    return (
        '<div class="status-block" id="{5}" data-report-status="{4}" data-report-count="{6}">'
        '<div class="status-title">'
        '<h3>{0}</h3>'
        '<span class="{1}">{2}</span>'
        '</div>'
        '{3}'
        '</div>'
    ).format(
        _escape(status),
        _get_status_badge_class(status),
        _escape(count),
        table,
        _escape(status),
        _get_status_dom_id(status),
        _escape(count),
    )


def _render_list_of_dicts(items):
    """
    Render a list of dictionaries as a table.

    :param list items: list of dict items
    :return: HTML table
    :rtype: str
    """

    columns = _get_columns(items)

    head = ''.join(
        '<th>{0}</th>'.format(_escape(column))
        for column in columns
    )

    rows = []

    for item in items:
        cells = ''.join(
            '<td>{0}</td>'.format(_render_cell(column, item.get(column)))
            for column in columns
        )
        rows.append(
            '<tr data-report-row data-row-search="{0}" data-report-url="{1}">{2}</tr>'.format(
                _escape(_get_item_search_text(item)),
                _escape(_get_item_url(item)),
                cells,
            )
        )

    return (
        '<div class="table-wrap">'
        '<table class="report-table">'
        '<thead><tr>{0}</tr></thead>'
        '<tbody>{1}</tbody>'
        '</table>'
        '</div>'
    ).format(head, ''.join(rows))


def _render_plain_list(items):
    """
    Render plain list values as a table.

    :param list items: list values
    :return: HTML table
    :rtype: str
    """

    rows = []

    for index, item in enumerate(items, start=1):
        rows.append(
            '<tr data-report-row data-row-search="{0}" data-report-url="{1}">'
            '<td><span class="badge">{2}</span></td>'
            '<td>{3}</td>'
            '</tr>'.format(
                _escape(_get_item_search_text(item)),
                _escape(_get_item_url(item)),
                index,
                _render_value(item),
            )
        )

    return (
        '<div class="table-wrap">'
        '<table class="report-table">'
        '<thead><tr><th>#</th><th>value</th></tr></thead>'
        '<tbody>{0}</tbody>'
        '</table>'
        '</div>'
    ).format(''.join(rows))


def _render_metadata(metadata):
    """
    Render additional report metadata.

    :param dict metadata: report metadata
    :return: HTML fragment
    :rtype: str
    """

    if not metadata:
        return ''

    rows = []

    for key in sorted(metadata.keys()):
        rows.append(
            '<tr>'
            '<th>{0}</th>'
            '<td>{1}</td>'
            '</tr>'.format(
                _escape(key),
                _render_value(metadata.get(key)),
            )
        )

    return (
        '<section class="section" id="metadata">'
        '<div class="section-header">'
        '<div>'
        '<h2>Metadata</h2>'
        '<p class="section-description">Additional scan context.</p>'
        '</div>'
        '</div>'
        '<div class="table-wrap">'
        '<table class="report-table">'
        '<tbody>{0}</tbody>'
        '</table>'
        '</div>'
        '</section>'
    ).format(''.join(rows))


def _render_cell(column, value):
    """
    Render a table cell value.

    :param str column: column name
    :param value: cell value
    :return: HTML fragment
    :rtype: str
    """

    if column == 'url' and _is_http_url(value):
        url = _escape(value)

        return (
            '<a class="mono break" href="{0}" target="_blank" rel="noopener noreferrer">'
            '{0}'
            '</a>'
        ).format(url)

    if column == 'code':
        return _render_status_code(value)

    if isinstance(value, bool):
        return _render_bool(value)

    if value is None:
        return '<span class="badge">-</span>'

    if isinstance(value, (dict, list, tuple)):
        return _render_nested_value(value)

    return '<span class="{0}">{1}</span>'.format(
        _get_value_class(column),
        _escape(value),
    )


def _render_value(value):
    """
    Render a generic value.

    :param value: value to render
    :return: HTML fragment
    :rtype: str
    """

    if isinstance(value, bool):
        return _render_bool(value)

    if value is None:
        return '<span class="badge">-</span>'

    if isinstance(value, dict):
        return _render_dict_value(value)

    if isinstance(value, (list, tuple)):
        return _render_list_value(value)

    return '<span class="break">{0}</span>'.format(_escape(value))


def _render_dict_value(value):
    """
    Render dictionary value as a collapsible JSON block.

    :param dict value: dictionary value
    :return: HTML fragment
    :rtype: str
    """

    if not value:
        return '<span class="badge">empty</span>'

    return _render_nested_value(value, open_by_default=True)


def _render_list_value(value):
    """
    Render list-like value as a collapsible JSON block.

    :param list|tuple value: list-like value
    :return: HTML fragment
    :rtype: str
    """

    if not value:
        return '<span class="badge">empty</span>'

    return _render_nested_value(value, open_by_default=True)


def _render_nested_value(value, open_by_default=False):
    """
    Render nested values without recursive tables.

    :param value: nested value
    :param bool open_by_default: whether the details block should be expanded
    :return: HTML fragment
    :rtype: str
    """

    open_attr = ' open' if open_by_default else ''

    return (
        '<details class="details-block"{0}>'
        '<summary>{1}</summary>'
        '<pre class="nested nested-json">{2}</pre>'
        '</details>'
    ).format(
        open_attr,
        _escape(_get_nested_summary(value)),
        _escape(_to_pretty_json(value)),
    )


def _get_nested_summary(value):
    """
    Return short summary for nested values.

    :param value: nested value
    :return: summary text
    :rtype: str
    """

    if isinstance(value, dict):
        return '{0} fields'.format(len(value))

    if isinstance(value, (list, tuple)):
        return '{0} items'.format(len(value))

    return 'details'


def _to_pretty_json(value):
    """
    Convert value to stable pretty JSON.

    :param value: value to convert
    :return: pretty JSON string
    :rtype: str
    """

    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)


def _render_status_code(value):
    """
    Render HTTP status code with visual severity.

    :param value: HTTP status code
    :return: HTML fragment
    :rtype: str
    """

    code = str(value)

    if code.startswith('2') or code.startswith('3'):
        badge_class = 'badge badge-success'
    elif code.startswith('4'):
        badge_class = 'badge badge-warning'
    elif code.startswith('5'):
        badge_class = 'badge badge-danger'
    else:
        badge_class = 'badge'

    return '<span class="{0}">{1}</span>'.format(badge_class, _escape(value))


def _render_bool(value):
    """
    Render boolean value as a badge.

    :param bool value: boolean value
    :return: HTML fragment
    :rtype: str
    """

    if value:
        return '<span class="badge badge-success">true</span>'

    return '<span class="badge">false</span>'


def _get_columns(items):
    """
    Return stable table columns for report item dictionaries.

    :param list items: report item dictionaries
    :return: ordered column names
    :rtype: list
    """

    preferred = [
        'url',
        'code',
        'size',
        'title',
        'redirect',
        'content_type',
        'waf',
        'waf_confidence',
        'bypass',
        'bypass_profile',
        'bypass_header',
        'bypass_value',
        'bypass_variant',
        'bypass_url',
        'bypass_from_status',
        'bypass_to_status',
        'bypass_from_code',
        'bypass_to_code',
        'bypass_score',
        'bypass_reasons',
        'stacktrace_detection',
        'secret_detection',
    ]

    existing = []

    for item in items:
        for key in item.keys():
            if key not in existing:
                existing.append(key)

    columns = [
        key
        for key in preferred
        if key in existing
    ]

    columns.extend([
        key
        for key in existing
        if key not in columns
    ])

    return columns



def _get_item_url(item):
    """
    Return the primary URL from a rendered finding item.

    :param item: report item
    :return: URL value or empty string
    :rtype: str
    """

    if isinstance(item, dict):
        value = item.get('url')
    else:
        value = item

    if _is_http_url(value):
        return value

    return ''


def _get_item_search_text(item):
    """
    Return stable searchable text for one report row.

    :param item: report item
    :return: normalized searchable text source
    :rtype: str
    """

    if isinstance(item, dict):
        values = []

        for key in sorted(item.keys()):
            values.append(key)
            values.append(_stringify_search_value(item.get(key)))

        return ' '.join(value for value in values if value)

    return _stringify_search_value(item)


def _stringify_search_value(value):
    """
    Convert a report value into text suitable for client-side filtering.

    :param value: report value
    :return: searchable text fragment
    :rtype: str
    """

    if value is None:
        return ''

    if isinstance(value, (dict, list, tuple)):
        return _to_pretty_json(value)

    return str(value)


def _get_status_dom_id(status):
    """
    Return a stable DOM id for a status group.

    :param str status: status bucket name
    :return: DOM id
    :rtype: str
    """

    slug = []

    for char in str(status).lower():
        if char.isalnum():
            slug.append(char)
        elif not slug or slug[-1] != '-':
            slug.append('-')

    value = ''.join(slug).strip('-') or 'unknown'

    return 'status-{0}'.format(value)


def _get_metadata(report_data):
    """
    Return report metadata excluding noisy item buckets.

    :param dict report_data: report payload
    :return: metadata map
    :rtype: dict
    """

    excluded = set(['items', 'report_items', 'total'])

    return {
        key: value
        for key, value in report_data.items()
        if key not in excluded
    }


def _get_status_badge_class(status):
    """
    Return badge CSS class for a finding status.

    :param str status: finding status
    :return: CSS class
    :rtype: str
    """

    status = str(status).lower()

    if status in ('success', 'index', 'indexof'):
        return 'badge badge-success'

    if status in ('failed', 'error', 'blocked'):
        return 'badge badge-danger'

    if status in ('warning', 'redirect'):
        return 'badge badge-warning'

    return 'badge'


def _get_value_class(column):
    """
    Return CSS class for a regular cell value.

    :param str column: column name
    :return: CSS class
    :rtype: str
    """

    if column in ('url', 'redirect', 'content_type', 'bypass_header', 'bypass_value', 'bypass_url'):
        return 'mono break'

    return 'break'


def _is_http_url(value):
    """
    Check whether value is a safe HTTP(S) URL for link rendering.

    :param value: candidate value
    :return: check result
    :rtype: bool
    """

    if not isinstance(value, str):
        return False

    return value.startswith('http://') or value.startswith('https://')


def _escape(value):
    """
    Escape value for safe HTML rendering.

    :param value: value to escape
    :return: escaped string
    :rtype: str
    """

    if value is None:
        return ''

    return xml_escape(str(value), {
        '"': '&quot;',
        "'": '&#x27;',
    })