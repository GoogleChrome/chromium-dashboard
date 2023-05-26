import testing_config
from internals.link_helpers import Link


class LinkHelperTest(testing_config.CustomTestCase):

    def test_parse_chromium_tracker(self):
        link = Link(
            'https://bugs.chromium.org/p/chromium/issues/detail?id=100000')
        link.parse()
        info = link.information
        assert info["summary"] == "Repeated zooms leave tearing artifact"
        assert info["statusRef"]["status"] == "Fixed"
        assert info["ownerRef"]["displayName"] == 'backer@chromium.org'

    def test_parse_chromium_tracker_fail_wrong_id(self):
        link = Link(
            'https://bugs.chromium.org/p/chromium/issues/details?id=100000000000000')
        link.parse()
        print(link.information)
        assert link.information == None and link.is_error == True

    def test_parse_chromium_tracker_fail_no_permission(self):
        link = Link('https://bugs.chromium.org/p/chromium/issues/detail?id=1')
        link.parse()
        assert link.information == None and link.is_error == True
