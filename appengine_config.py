# Add libraries to pkg_resources working set to find the distribution.  # noqa: D100, E501
import pkg_resources

pkg_resources.working_set.add_entry(lib_path)  # noqa: F821
