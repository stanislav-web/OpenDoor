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

    Development Team: Stanislav WEB
"""


class Config(object):

    """Config class"""

    templates = {
        'unsupported': 'Your Python version v{actual} is not supported by this application. Please consider {expected}',
        'abort': 'Session canceled',
        'upd_win_stat': 'Win OS does not support --update inside.\nPlease run your GIT binary to fetch data manualy',
        'use_reports': 'Use --report param to store your scan results',
        'load_wizard': 'Load wizard options from : {config}',
        'report': '{plugin} : {dest}',
        'logged': 'Scanned host has been reported. Press ENTER to rescan or CTRL+C to exit: ',
        'checking_connect': 'Wait, please, checking connect to -> {host}:{port} ...',
        'slow_connection': 'Too slow connection. Please decrease the num of threads and increase the request timeout',
        'online': 'Server {host}:{port} ({ip}) is online!',
        'create_queue_progress': 'Create queue {bar}',
        'scanning': 'Scanning {host} ...',
        'debug': 'Starting debug level {level}. Using scan method: {method} ...',
        'indexof_act': 'Apache index of/ pages detecting',
        'randomizing': 'Randomizing scan list ...',
        'browser': 'Fetching user-agent: {browser}',
        'directories': 'Read {total} directories list by line',
        'ext_filter': 'Read {total} directories list by filter: {ext}',
        'create_queue': 'Creating queue with {threads} thread(s)...',
        'subdomains': 'Read {total} subdomains list by line...',
        'random_browser': 'Fetching random user-agent per request...',
        'total_time_lvl3': 'Total time running: {time}',
        'thread_limit': 'Threads has been reduced to {max} (max) instead of {threads}',
        'stop_threads': 'Stopping threads ({threads})...',
        'option_prompt': 'Press "[C]ontinue" to resume or "[E]xit" to abort session: ',
        'resume_threads': 'Resuming scan...',
        'get_item': '{percent} [{current}/{total}] - {size} - {item}',
        'ignored_item': 'skip [{current}/{total}] - Ignored {item}',
        'max_retry_error': 'skip. Max retries exceeded: {url}',
        'addtopool': 'Adding {total} lines to queue...',
        'http_pool_start': 'Using HTTP keep-alive connection',
        'https_pool_start': 'Using SSL keep-alive connection',
        'proxy_pool_standalone': 'Using custom proxy server: {server}',
        'proxy_pool_internal_start': 'Fetching internal proxy list...',
        'proxy_pool_external_start': 'Fetching external proxy list...',
        'request_header_dbg': 'Request header:\n{dbg}',
        'response_header_dbg': 'Response header:\n{dbg}',
        'ignored_path': 'Ignored. The path {path} in ignore list',
        'proxy_max_retry_error': 'Skipped. Proxy {proxy} Max retries exceeded: {url}',
        'host_changed_error': 'Block external redirect -> {details}',
        'read_timeout_error': 'Connection timeout! {url}. Increase using --timeout option',
        'certificat': 'Cert required {url}',
        'success': 'OK {url}',
        'file': 'File {url}',
        'indexof': 'Index {url}',
        'forbidden': 'Denied {url}',
        'auth': 'Auth {url}',
        'redirect': 'R {url} -> {rurl}'
    }
