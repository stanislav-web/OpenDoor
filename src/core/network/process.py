# -*- coding: utf-8 -*-

"""
    Process runner for network transports.
"""

import subprocess

from urllib3 import PoolManager, Timeout, disable_warnings
from urllib3.exceptions import HTTPError, InsecureRequestWarning

from .exceptions import NetworkTransportError


class ProcessRunner(object):

    """Process runner wrapper."""

    def start_persistent(self, command):
        """
        Start a long-running process.

        :param list[str] command:
        :raise NetworkTransportError:
        :return: subprocess.Popen
        """

        try:
            return subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        except OSError as error:
            raise NetworkTransportError(error)

    def run(self, command, timeout=30):
        """
        Run a short-lived command.

        :param list[str] command:
        :param int timeout:
        :raise NetworkTransportError:
        :return: subprocess.CompletedProcess
        """

        try:
            return subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=True
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise NetworkTransportError(error)

    def healthcheck(self, url, timeout=5):
        """
        Validate network connectivity through the active OS route.

        Any HTTP response means the route is usable; transport-level errors
        are wrapped and retried by the transport manager.

        :param str url: Healthcheck URL.
        :param int timeout: Request timeout in seconds.
        :raise NetworkTransportError:
        :return: int HTTP status code.
        """

        manager = None
        disable_warnings(InsecureRequestWarning)

        try:
            manager = PoolManager(
                timeout=Timeout(connect=timeout, read=timeout),
                cert_reqs='CERT_NONE',
            )
            response = manager.request(
                'GET',
                url,
                preload_content=False,
                retries=False,
                redirect=False,
            )
            status = response.status
            response.release_conn()
            return status
        except (HTTPError, OSError, ValueError) as error:
            raise NetworkTransportError(error)
        finally:
            if manager is not None:
                manager.clear()

    def stop(self, process, timeout=5):
        """
        Stop a persistent process.

        :param subprocess.Popen|object process:
        :param int timeout:
        :raise NetworkTransportError:
        :return: None
        """

        if process is None:
            return

        try:
            if process.poll() is not None:
                return

            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=timeout)
        except (OSError, subprocess.SubprocessError) as error:
            raise NetworkTransportError(error)
