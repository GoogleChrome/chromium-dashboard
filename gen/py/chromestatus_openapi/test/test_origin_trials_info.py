# coding: utf-8

"""
    chomestatus API

    The API for chromestatus.com. chromestatus.com is the official tool used for tracking feature launches in Blink (the browser engine that powers Chrome and many other web browsers). This tool guides feature owners through our launch process and serves as a primary source for developer information that then ripples throughout the web developer ecosystem. More details at: https://github.com/GoogleChrome/chromium-dashboard

    The version of the OpenAPI document: 1.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from chromestatus_openapi.models.origin_trials_info import OriginTrialsInfo

class TestOriginTrialsInfo(unittest.TestCase):
    """OriginTrialsInfo unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> OriginTrialsInfo:
        """Test OriginTrialsInfo
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `OriginTrialsInfo`
        """
        model = OriginTrialsInfo()
        if include_optional:
            return OriginTrialsInfo(
                id = '',
                display_name = '',
                description = '',
                origin_trial_feature_name = '',
                enabled = True,
                status = '',
                chromestatus_url = '',
                start_milestone = '',
                end_milestone = '',
                original_end_milestone = '',
                end_time = '',
                documentation_url = '',
                feedback_url = '',
                intent_to_experiment_url = '',
                trial_extensions = [
                    None
                    ],
                type = '',
                allow_third_party_origins = True
            )
        else:
            return OriginTrialsInfo(
        )
        """

    def testOriginTrialsInfo(self):
        """Test OriginTrialsInfo"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
