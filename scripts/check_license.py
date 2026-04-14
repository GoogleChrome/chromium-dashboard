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

"""Checks and enforces Apache 2.0 license headers across project files.

This script scans specified directories for Python, JavaScript, TypeScript,
and HTML files. It verifies that each file contains the Apache 2.0 license
header. It can also automatically inject missing headers using the `--fix` flag.
"""

import argparse
import datetime
import os
import sys

YEAR = datetime.datetime.now().year

PY_LICENSE = f"""# Copyright {YEAR} Google LLC
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
"""

JS_LICENSE = f"""/**
 * Copyright {YEAR} Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
"""

HTML_LICENSE = f"""<!--
Copyright {YEAR} Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
"""

DIRECTORIES = [
    'api',
    'client-src',
    'internals',
    'pages',
    'framework',
    'scripts',
]
EXTENSIONS = {
    '.py': PY_LICENSE,
    '.js': JS_LICENSE,
    '.ts': JS_LICENSE,
    '.html': HTML_LICENSE,
}

# Directories or files to explicitly ignore if necessary
IGNORE_DIRS = ['node_modules', 'venv', 'cs-env', 'testdata', 'gen']


def check_license(fix=False, directories=DIRECTORIES, exit_on_fail=True):
    """Checks for and optionally fixes missing license headers in files.

    Args:
        fix: If True, injects the license header into files missing it.
        directories: A list of directory paths to scan.
        exit_on_fail: If True, calls sys.exit() with status code 1 when missing
            licenses are found (and not fixed). Useful for CI/CD pipelines.

    Returns:
        A list of file paths that are missing the license header.
    """
    missing_license = []

    for directory in directories:
        if not os.path.exists(directory):
            continue
        for root, dirs, files in os.walk(directory):
            # Modify dirs in-place to avoid traversing ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in EXTENSIONS:
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if (
                        'Licensed under the Apache License, Version 2.0'
                        not in content
                    ):
                        missing_license.append(filepath)

    if not fix:
        if missing_license:
            print('The following files are missing the Apache license:')
            for f in missing_license:
                print(f'  {f}')
            print('\nRun `make lint-fix` (or script with --fix) to add them.')
            if exit_on_fail:
                sys.exit(1)
        else:
            print('All files have the Apache license.')
            if exit_on_fail:
                sys.exit(0)
    else:
        if missing_license:
            for filepath in missing_license:
                ext = os.path.splitext(filepath)[1]
                template = EXTENSIONS[ext]

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Special handling for scripts that might have a shebang or encoding comment
                lines = content.splitlines(keepends=True)
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('#!') or line.startswith('# -*-'):
                        insert_idx = i + 1
                    else:
                        break

                new_content = (
                    ''.join(lines[:insert_idx])
                    + template
                    + '\n'
                    + ''.join(lines[insert_idx:])
                )

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            print(f'Added license to {len(missing_license)} files.')
        else:
            print('All files already have the Apache license.')

    return missing_license


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Check or fix missing Apache license headers.'
    )
    parser.add_argument(
        '--fix', action='store_true', help='Fix missing licenses'
    )
    args = parser.parse_args()
    check_license(fix=args.fix)
