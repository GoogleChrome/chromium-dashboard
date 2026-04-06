# Add libraries to pkg_resources working set to find the distribution.
"""Configuration module for Google App Engine environment setup."""

import pkg_resources

pkg_resources.working_set.add_entry(lib_path)  # noqa: F821
