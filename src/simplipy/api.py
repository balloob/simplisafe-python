"""
Access to the SimpliSafe API.
"""
import uuid
import logging
import json

import requests

# from simplipy.system import SimpliSafeSystem

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.simplisafe.com/v1/"
# Requires BasicAuth
TOKEN_URL = BASE_URL + "api/token"
AUTH_CHECK_URL = BASE_URL + "api/authCheck"
USERS_SUBSCRIPTIONS_URL = BASE_URL + "users/{}/subscriptions?activeOnly=true"
SUBSCRIPTION_URL = BASE_URL + "subscriptions/{}/"

DEVICE_ID = "ANDROID; UserAgent=unknown Android SDK built for x86; Serial=unknown; ID=e36659c47cce2843;:"
USER_AGENT = "SimpliSafe Android App Build 20207"
CONTENT_TYPE = "application/json; charset=UTF-8"

HEADERS = {"User-Agent": USER_AGENT, "Content-Type": CONTENT_TYPE}
OAUTH_HEADERS = HEADERS

BASIC_AUTH_STRING = "NWYwNmY1YzktMDJkOS00ZDY2LTg3ZmUtZWRiZWQ2N2ZiMDE0LjIwMjA3LmFuZHJvaWQuc2ltcGxpc2FmZS5jb206"
BASIC_AUTH_HEADERS = HEADERS


class SimpliSafeApiInterface(object):
    """
    Object used for talking to the SimpliSafe API.
    """

    def __init__(self, username, password, basic_auth=None):
        """
        Create the interface to the API.
        """
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.sids = {}
        if basic_auth is not None:
            BASIC_AUTH_HEADERS["Authorization"] = "Basic " + basic_auth
        else:
            BASIC_AUTH_HEADERS["Authorization"] = "Basic " + BASIC_AUTH_STRING
        if self._get_token() and self._get_user_id() and self._get_subscriptions():
        	_LOGGER.info("Setup complete")
        else:
        	_LOGGER.error("Failed to complete setup")

    def _get_token(self):
        """
        Get an Oauth token from the API.
        """

        login_data = {
            'device_id': DEVICE_ID,
            'grant_type': "password",
            'username': self.username,
            'password': self.password
        }


        response = requests.post(TOKEN_URL, data=json.dumps(login_data),
                                 headers=BASIC_AUTH_HEADERS, verify=False)
        _LOGGER.debug(response.content)
        print(response.status_code)
        if response.status_code != 200:
            _LOGGER.error("Invalid username or password")
            return False
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.access_token = _json.get("access_token")
        self.refresh_token = _json.get("refresh_token")

        _LOGGER.info("Logged into SimpliSafe")
        return True

    def _get_user_id(self):
        """Get user ID."""

        OAUTH_HEADERS["Authorization"] = "Bearer {}".format(self.access_token)
        print(str(OAUTH_HEADERS))

        response = requests.get(AUTH_CHECK_URL, headers=OAUTH_HEADERS, verify=False)
        _LOGGER.debug(response.content)
        if response.status_code != 200:
            _LOGGER.error("Failed to get user ID")
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.user_id = _json.get("userId")
        return True


    def _get_subscriptions(self):
        """Get a list of a sids."""

        response = requests.get(USERS_SUBSCRIPTIONS_URL.format(self.user_id), headers=OAUTH_HEADERS, verify=False)
        _LOGGER.debug(response.content)
        if response.status_code != 200:
            _LOGGER.error("Failed to get subscriptions")
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.sids = _json.get("subscriptions")


    def set_system_state(self, location_id, state):
        """
        Set the state of the alarm system.

        Args:
            location_id (int): The location id to change the state of.
            state (str): The state to set. One of ['home', 'away', 'off']
        Returns (boolean): True or False (Was the command successful)
        """

        _url = SUBSCRIPTION_URL.format(location_id) + "/state?state=" + state

        response = requests.post(_url, verify=False)
        _LOGGER.debug(response.content)
        for subscription in self.sids:
            if subscription["sid"] == location_id:
                _log_string = "Failed to set {} state to {}".format(subscription["location"]["street1"], state)
        if response.status_code != 200:
            _LOGGER.error(_log_string)
            return False
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        if _json.get("success"):
            return True
        else:
            _log_string = _log_string + " " + _json.get("reason")
            _LOGGER.error(_log_string)
            return False

    def get_system_state(self, location_id):
        """
        Get the location_id's current system state.

        Args:
            location_id (str): The id of the location
        Returns: (dictionary): System
        """
        for subscription in self.sids:
            if subscription["sid"] == location_id:
                return subscription["location"]["system"]


def get_systems(api_interface):
    """
    Gets the locations from the API and returns objects for each.

    Returns (dictions): Returns a diction of SimpliSafeSystem objects.
    """
    systems = {}

    for subscription in api_interface.sids:
        systems[subscription["sid"]] = api_interface.get_system_state(subscription["sid"])

    return systems