# -*- coding: utf-8 -*-

"""Message class"""

class Message:
    """Message helper class"""

    def __init__(self):
        self.dictionary = {
            'file_detected' : "Probably you found important filesource {0} {1}"
        }

    def get(self, key):
        """ Get row message by key"""

        row = ''
        if key in self.dictionary:
            row = self.dictionary[key]
        return row
