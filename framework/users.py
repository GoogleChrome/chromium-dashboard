
from flask import session
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from settings import UNIT_TEST_MODE

class User(object):
    """Provides the email address, nickname, and ID for a user.

    A nickname is a human-readable string that uniquely identifies a Google user,
    akin to a username. For some users, this nickname is an email address, but for
    other users, a different nickname is used.

    A user is a Google Accounts user.

    `federated_identity` and `federated_provider` are decommissioned and should
    not be used.

    This class is based on google.appengine.api.users.User class 
    """





    __user_id = None
    __federated_identity = None
    __federated_provider = None

    def __init__(self, email=None, _auth_domain=None,
                _user_id=None, federated_identity=None, federated_provider=None,
                _strict_mode=True):
        """Constructor.

        Args:
        email: An optional string of the user's email address. It defaults to
            the current user's email address.
        federated_identity: Decommissioned, don't use.
        federated_provider: Decommissioned, don't use.

        Raises:
        UserNotFoundError: If the user is not logged in and both `email` and
            `federated_identity` are empty.
        """

        self.__email = email
        self.__federated_identity = federated_identity
        self.__federated_provider = federated_provider
        self.__auth_domain = _auth_domain
        self.__user_id = _user_id or None


    def nickname(self):
        """Returns the user's nickname.

        The nickname will be a unique, human readable identifier for this user with
        respect to this application. It will be an email address for some users,
        and part of the email address for some users.

        Returns:
        The nickname of the user as a string.
        """
        if (self.__email and self.__auth_domain and
            self.__email.endswith('@' + self.__auth_domain)):
            suffix_len = len(self.__auth_domain) + 1
            return self.__email[:-suffix_len]
        elif self.__federated_identity:
            return self.__federated_identity
        else:
            return self.__email


    def email(self):
        """Returns the user's email address."""
        return self.__email


    def user_id(self):
        """Obtains the user ID of the user.

        Returns:
        A permanent unique identifying string or `None`. If the email address was
        set explicity, this will return `None`.
        """
        return self.__user_id


    def auth_domain(self):
        """Obtains the user's authentication domain.

        Returns:
        A string containing the authentication domain. This method is internal and
        should not be used by client applications.
        """
        return self.__auth_domain


    def federated_identity(self):
        """Decommissioned, don't use.

        Returns:
        A string containing the federated identity of the user. If the user is not
        a federated user, `None` is returned.
        """
        return self.__federated_identity


    def federated_provider(self):
        """Decommissioned, don't use.

        Returns:
        A string containing the federated provider. If the user is not a federated
        user, `None` is returned.
        """
        return self.__federated_provider


    def __unicode__(self):
        return six_subset.text_type(self.nickname())

    def __str__(self):
        return str(self.nickname())

    def __repr__(self):
        values = []
        if self.__email:
            values.append("email='%s'" % self.__email)
        if self.__federated_identity:
            values.append("federated_identity='%s'" % self.__federated_identity)
        if self.__user_id:
            values.append("_user_id='%s'" % self.__user_id)
        return 'users.User(%s)' % ','.join(values)

    def __hash__(self):
        if self.__federated_identity:
            return hash((self.__federated_identity, self.__auth_domain))
        else:
            return hash((self.__email, self.__auth_domain))

    def __cmp__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        if self.__federated_identity:
            return cmp((self.__federated_identity, self.__auth_domain),
                        (other.__federated_identity, other.__auth_domain))
        else:
            return cmp((self.__email, self.__auth_domain),
                        (other.__email, other.__auth_domain))

    def get_current_user():
        """Retrieves information associated with the user that is making a request.

        Returns:

        """
        try:
            return User()
        except UserNotFoundError:
            return None


    def is_current_user_admin():
        """Specifies whether the user making a request is an application admin.

        Because administrator status is not persisted in the datastore,
        `is_current_user_admin()` is a separate function rather than a member function
        of the `User` class. The status only exists for the user making the current
        request.

        Returns:
        `True` if the user is an administrator; all other user types return `False`.
        """

        # This environment variable was set by GAE based on a GAE session cookie. 
        # With Google Sign-In, it will probably never be present. Hence, currently is always False
        # TODO (jrobbins): Implement this method 
        return (os.environ.get('USER_IS_ADMIN', '0')) == '1'


def get_current_user():

    if UNIT_TEST_MODE:
        if os.environ['USER_EMAIL']!= '':
            current_user = User(email=os.environ['USER_EMAIL'], _user_id=os.environ['USER_ID'])
        else:
            current_user = None
        return current_user

    token = session.get('id_token')
    current_user = None
    if token:
      try:
        CLIENT_ID = '77756740465-e5r4o15qg4hkdfiucjpl231o79k3ipjv.apps.googleusercontent.com'
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        current_user = User(email=idinfo['email'], _user_id=idinfo['sub'])

      except ValueError:
          # Remove the id_token from session if it is invalid or expired
          session.clear()
          current_user = None
          pass

    return current_user


def is_current_user_admin():
    return False