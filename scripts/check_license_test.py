# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
import tempfile
import shutil
from scripts.check_license import check_license, PY_LICENSE, JS_LICENSE, HTML_LICENSE

class CheckLicenseTest(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_all_files_have_licenses(self):
        # Create valid python and JS files
        py_file = os.path.join(self.test_dir, 'valid.py')
        js_file = os.path.join(self.test_dir, 'valid.js')

        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(PY_LICENSE + "\nprint('hello world')")
            
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(JS_LICENSE + "\nconsole.log('hello');")
            
        missing = check_license(fix=False, directories=[self.test_dir], exit_on_fail=False)
        self.assertEqual(len(missing), 0)

    def test_missing_licenses_detected(self):
        # Create invalid files
        py_file = os.path.join(self.test_dir, 'invalid.py')
        ts_file = os.path.join(self.test_dir, 'invalid.ts')

        with open(py_file, 'w', encoding='utf-8') as f:
            f.write("print('no license here')")
            
        with open(ts_file, 'w', encoding='utf-8') as f:
            f.write("const x: number = 5;")
            
        missing = check_license(fix=False, directories=[self.test_dir], exit_on_fail=False)
        self.assertEqual(len(missing), 2)
        self.assertIn(py_file, missing)
        self.assertIn(ts_file, missing)

    def test_fix_adds_license(self):
        # Create an invalid py file
        py_file = os.path.join(self.test_dir, 'to_fix.py')
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write("def do_something():\n    pass")

        # Run with fix=True
        missing = check_license(fix=True, directories=[self.test_dir], exit_on_fail=False)
        
        # It should have returned the list of files it detected as missing
        self.assertEqual(len(missing), 1)
        
        # Verify the file was actually fixed
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn('Licensed under the Apache License, Version 2.0', content)
        self.assertIn('def do_something():', content)

    def test_fix_respects_shebang(self):
        py_file = os.path.join(self.test_dir, 'script.py')
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write("#!/usr/bin/env python\n# -*- coding: utf-8 -*-\nprint('start')")

        check_license(fix=True, directories=[self.test_dir], exit_on_fail=False)
        
        with open(py_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # The first two lines should still be the shebang and encoding
        self.assertTrue(lines[0].startswith('#!'))
        self.assertTrue(lines[1].startswith('# -*-'))
        # The license should be injected immediately after
        self.assertIn('Copyright', lines[2])

    def test_ignores_specified_directories(self):
        # Create an ignored node_modules directory
        ignored_dir = os.path.join(self.test_dir, 'node_modules')
        os.makedirs(ignored_dir)
        
        js_file = os.path.join(ignored_dir, 'invalid.js')
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write("console.log('ignored');")

        # It shouldn't detect this missing license because it's in node_modules
        missing = check_license(fix=False, directories=[self.test_dir], exit_on_fail=False)
        self.assertEqual(len(missing), 0)

if __name__ == '__main__':
    unittest.main()
