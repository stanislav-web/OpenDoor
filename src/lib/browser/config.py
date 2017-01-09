# -*- coding: utf-8 -*-

"""Config classes """

class Config:
    """Config class"""

    def __init__(self, params):
        """ read filtered input params """

        self._scan = params.get('scan')
        self._host = params.get('host')
        self._port = params.get('port')
        self._is_indexof = params.get('indexof')
        self._method = params.get('method') if params.get('indexof') is None else 'GET'
        self._threads = params.get('threads')
        self._delay = 0 if params.get('delay')is None else params.get('delay')
        self._timeout =  0 if params.get('timeout')is None else params.get('timeout')
        self._threads = params.get('threads')
        self._debug = params.get('debug')
        self._is_proxy = params.get('tor')
        self._is_random_user_agent = params.get('random_agent')
        self._user_agent = 'Opendoor OWASP'



