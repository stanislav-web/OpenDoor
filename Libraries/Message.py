# -*- coding: utf-8 -*-

"""Message class"""


class Message:
    """Message class"""

    def __init__(self):
        self.dictionary = {
            'online'        :   "Server {0} {1}:{2} is online",
            'offline'       :   "Oops Error occured, Server offline or invalid URL. Reason: {}",
            'redirect'      :   "Redirect {0} --> {1}",
            'scanning'      :   "Scanning {0} ...",
            'abort'         :   "Session canceled",
            'excluded'      :   "Excluded path: {0}",
            'unresponsible' :   "Unresponsible path : {0}",
            'use_log'       :   "Use --log param to save scan result",
            'max_threads'   :   "Passed {0} threads max for your possibility",
            'file_detected' :   "Probably you found important filesource {0} {1}"
        }

    def get(self, key):
        """ Get row message by key"""

        row = ''
        if key in self.dictionary:
            row = self.dictionary[key]
        return row
