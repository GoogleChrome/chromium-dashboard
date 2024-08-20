from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from chromestatus_openapi.models.base_model import Model
from chromestatus_openapi.models.feature_dict_inner_browser_status import FeatureDictInnerBrowserStatus
from chromestatus_openapi import util

from chromestatus_openapi.models.feature_dict_inner_browser_status import FeatureDictInnerBrowserStatus  # noqa: E501

class FeatureDictInnerChromeBrowserInfo(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, bug=None, blink_components=None, devrel=None, owners=None, origintrial=None, intervention=None, prefixed=None, flag=None, status=None, desktop=None, android=None, webview=None, ios=None):  # noqa: E501
        """FeatureDictInnerChromeBrowserInfo - a model defined in OpenAPI

        :param bug: The bug of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type bug: str
        :param blink_components: The blink_components of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type blink_components: List[str]
        :param devrel: The devrel of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type devrel: List[str]
        :param owners: The owners of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type owners: List[str]
        :param origintrial: The origintrial of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type origintrial: bool
        :param intervention: The intervention of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type intervention: bool
        :param prefixed: The prefixed of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type prefixed: bool
        :param flag: The flag of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type flag: str
        :param status: The status of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type status: FeatureDictInnerBrowserStatus
        :param desktop: The desktop of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type desktop: int
        :param android: The android of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type android: int
        :param webview: The webview of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type webview: int
        :param ios: The ios of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :type ios: int
        """
        self.openapi_types = {
            'bug': str,
            'blink_components': List[str],
            'devrel': List[str],
            'owners': List[str],
            'origintrial': bool,
            'intervention': bool,
            'prefixed': bool,
            'flag': str,
            'status': FeatureDictInnerBrowserStatus,
            'desktop': int,
            'android': int,
            'webview': int,
            'ios': int
        }

        self.attribute_map = {
            'bug': 'bug',
            'blink_components': 'blink_components',
            'devrel': 'devrel',
            'owners': 'owners',
            'origintrial': 'origintrial',
            'intervention': 'intervention',
            'prefixed': 'prefixed',
            'flag': 'flag',
            'status': 'status',
            'desktop': 'desktop',
            'android': 'android',
            'webview': 'webview',
            'ios': 'ios'
        }

        self._bug = bug
        self._blink_components = blink_components
        self._devrel = devrel
        self._owners = owners
        self._origintrial = origintrial
        self._intervention = intervention
        self._prefixed = prefixed
        self._flag = flag
        self._status = status
        self._desktop = desktop
        self._android = android
        self._webview = webview
        self._ios = ios

    @classmethod
    def from_dict(cls, dikt) -> 'FeatureDictInnerChromeBrowserInfo':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FeatureDictInnerChromeBrowserInfo of this FeatureDictInnerChromeBrowserInfo.  # noqa: E501
        :rtype: FeatureDictInnerChromeBrowserInfo
        """
        return util.deserialize_model(dikt, cls)

    @property
    def bug(self) -> str:
        """Gets the bug of this FeatureDictInnerChromeBrowserInfo.


        :return: The bug of this FeatureDictInnerChromeBrowserInfo.
        :rtype: str
        """
        return self._bug

    @bug.setter
    def bug(self, bug: str):
        """Sets the bug of this FeatureDictInnerChromeBrowserInfo.


        :param bug: The bug of this FeatureDictInnerChromeBrowserInfo.
        :type bug: str
        """

        self._bug = bug

    @property
    def blink_components(self) -> List[str]:
        """Gets the blink_components of this FeatureDictInnerChromeBrowserInfo.


        :return: The blink_components of this FeatureDictInnerChromeBrowserInfo.
        :rtype: List[str]
        """
        return self._blink_components

    @blink_components.setter
    def blink_components(self, blink_components: List[str]):
        """Sets the blink_components of this FeatureDictInnerChromeBrowserInfo.


        :param blink_components: The blink_components of this FeatureDictInnerChromeBrowserInfo.
        :type blink_components: List[str]
        """

        self._blink_components = blink_components

    @property
    def devrel(self) -> List[str]:
        """Gets the devrel of this FeatureDictInnerChromeBrowserInfo.


        :return: The devrel of this FeatureDictInnerChromeBrowserInfo.
        :rtype: List[str]
        """
        return self._devrel

    @devrel.setter
    def devrel(self, devrel: List[str]):
        """Sets the devrel of this FeatureDictInnerChromeBrowserInfo.


        :param devrel: The devrel of this FeatureDictInnerChromeBrowserInfo.
        :type devrel: List[str]
        """

        self._devrel = devrel

    @property
    def owners(self) -> List[str]:
        """Gets the owners of this FeatureDictInnerChromeBrowserInfo.


        :return: The owners of this FeatureDictInnerChromeBrowserInfo.
        :rtype: List[str]
        """
        return self._owners

    @owners.setter
    def owners(self, owners: List[str]):
        """Sets the owners of this FeatureDictInnerChromeBrowserInfo.


        :param owners: The owners of this FeatureDictInnerChromeBrowserInfo.
        :type owners: List[str]
        """

        self._owners = owners

    @property
    def origintrial(self) -> bool:
        """Gets the origintrial of this FeatureDictInnerChromeBrowserInfo.


        :return: The origintrial of this FeatureDictInnerChromeBrowserInfo.
        :rtype: bool
        """
        return self._origintrial

    @origintrial.setter
    def origintrial(self, origintrial: bool):
        """Sets the origintrial of this FeatureDictInnerChromeBrowserInfo.


        :param origintrial: The origintrial of this FeatureDictInnerChromeBrowserInfo.
        :type origintrial: bool
        """

        self._origintrial = origintrial

    @property
    def intervention(self) -> bool:
        """Gets the intervention of this FeatureDictInnerChromeBrowserInfo.


        :return: The intervention of this FeatureDictInnerChromeBrowserInfo.
        :rtype: bool
        """
        return self._intervention

    @intervention.setter
    def intervention(self, intervention: bool):
        """Sets the intervention of this FeatureDictInnerChromeBrowserInfo.


        :param intervention: The intervention of this FeatureDictInnerChromeBrowserInfo.
        :type intervention: bool
        """

        self._intervention = intervention

    @property
    def prefixed(self) -> bool:
        """Gets the prefixed of this FeatureDictInnerChromeBrowserInfo.


        :return: The prefixed of this FeatureDictInnerChromeBrowserInfo.
        :rtype: bool
        """
        return self._prefixed

    @prefixed.setter
    def prefixed(self, prefixed: bool):
        """Sets the prefixed of this FeatureDictInnerChromeBrowserInfo.


        :param prefixed: The prefixed of this FeatureDictInnerChromeBrowserInfo.
        :type prefixed: bool
        """

        self._prefixed = prefixed

    @property
    def flag(self) -> str:
        """Gets the flag of this FeatureDictInnerChromeBrowserInfo.


        :return: The flag of this FeatureDictInnerChromeBrowserInfo.
        :rtype: str
        """
        return self._flag

    @flag.setter
    def flag(self, flag: str):
        """Sets the flag of this FeatureDictInnerChromeBrowserInfo.


        :param flag: The flag of this FeatureDictInnerChromeBrowserInfo.
        :type flag: str
        """

        self._flag = flag

    @property
    def status(self) -> FeatureDictInnerBrowserStatus:
        """Gets the status of this FeatureDictInnerChromeBrowserInfo.


        :return: The status of this FeatureDictInnerChromeBrowserInfo.
        :rtype: FeatureDictInnerBrowserStatus
        """
        return self._status

    @status.setter
    def status(self, status: FeatureDictInnerBrowserStatus):
        """Sets the status of this FeatureDictInnerChromeBrowserInfo.


        :param status: The status of this FeatureDictInnerChromeBrowserInfo.
        :type status: FeatureDictInnerBrowserStatus
        """

        self._status = status

    @property
    def desktop(self) -> int:
        """Gets the desktop of this FeatureDictInnerChromeBrowserInfo.


        :return: The desktop of this FeatureDictInnerChromeBrowserInfo.
        :rtype: int
        """
        return self._desktop

    @desktop.setter
    def desktop(self, desktop: int):
        """Sets the desktop of this FeatureDictInnerChromeBrowserInfo.


        :param desktop: The desktop of this FeatureDictInnerChromeBrowserInfo.
        :type desktop: int
        """

        self._desktop = desktop

    @property
    def android(self) -> int:
        """Gets the android of this FeatureDictInnerChromeBrowserInfo.


        :return: The android of this FeatureDictInnerChromeBrowserInfo.
        :rtype: int
        """
        return self._android

    @android.setter
    def android(self, android: int):
        """Sets the android of this FeatureDictInnerChromeBrowserInfo.


        :param android: The android of this FeatureDictInnerChromeBrowserInfo.
        :type android: int
        """

        self._android = android

    @property
    def webview(self) -> int:
        """Gets the webview of this FeatureDictInnerChromeBrowserInfo.


        :return: The webview of this FeatureDictInnerChromeBrowserInfo.
        :rtype: int
        """
        return self._webview

    @webview.setter
    def webview(self, webview: int):
        """Sets the webview of this FeatureDictInnerChromeBrowserInfo.


        :param webview: The webview of this FeatureDictInnerChromeBrowserInfo.
        :type webview: int
        """

        self._webview = webview

    @property
    def ios(self) -> int:
        """Gets the ios of this FeatureDictInnerChromeBrowserInfo.


        :return: The ios of this FeatureDictInnerChromeBrowserInfo.
        :rtype: int
        """
        return self._ios

    @ios.setter
    def ios(self, ios: int):
        """Sets the ios of this FeatureDictInnerChromeBrowserInfo.


        :param ios: The ios of this FeatureDictInnerChromeBrowserInfo.
        :type ios: int
        """

        self._ios = ios
