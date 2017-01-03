# -*- coding: utf-8 -*-

"""Message class"""


class Message:
    """Message class"""

    dictionary = {
            'online'        :   "Server {0} {1}:{2} is online",
            'offline'       :   "Oops Error occured, Server offline or invalid URL. Reason: {}",
            'redirect'      :   "Redirect {0} --> {1}",
            'scanning'      :   "Scanning {0} ...",
            'abort'         :   "Session canceled",
            'timeout'       :   "Connection timeout: {0} . Try to increase --delay between requests",
            'excluded'      :   "Excluded path: {0}",
            'unresponsible' :   "Unresponsible path : {0}",
            'use_log'       :   "Use --log param to save scan result",
            'max_threads'   :   "Passed {0} threads max for your possibility",
            'has_scanned'   :   "You already have the results for {0} saved in logs directory.\nWould you like to rescan? Press [ENTER] to continue: ",
            'file_detected' :   "Probably you found important filesource {0} {1}"
        }

    @staticmethod
    def get(key):
        """ Get row message by key"""

        row = ''
        if key in Message.dictionary:
            row = Message.dictionary[key]
        return row
