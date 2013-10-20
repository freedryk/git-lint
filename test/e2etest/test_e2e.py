# Copyright 2013 Sebastian Kreft
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
import shutil
import subprocess
import tempfile
import unittest

import gitlint.linters as linters


class E2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_cwd = os.getcwd() 
        cls.temp_directory = tempfile.mkdtemp(prefix='gitlint')
        os.chdir(cls.temp_directory)
        subprocess.check_output(['git', 'init'], stderr=subprocess.STDOUT)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_directory, True)
        os.chdir(cls.original_cwd)

    def test_linters(self):
        for extension, linter_list in linters._EXTENSION_TO_LINTER.iteritems():
            for linter in linter_list:
                print extension, linter
                self.assert_linter_works(linter.args[0], [extension])

    def test_extension_not_defined(self):
        extension = max(linters._EXTENSION_TO_LINTER.keys()) + 'fake'
        filename = os.path.join(self.temp_directory, 'filename' + extension)
        with open(filename, 'w') as f:
            f.write('Foo')
        subprocess.check_output(['git', 'add', filename], stderr=subprocess.STDOUT)
        output = subprocess.check_output(['git', 'lint'], stderr=subprocess.STDOUT)

        self.assertIn(os.path.relpath(filename), output)
        self.assertIn('SKIPPED', output)
        self.assertIn(extension, output)

    # TODO(skreft): improves assert so the message is clear in case there's an error ()include output and file that is being processed.
    # TODO(skreft): maybe call the script directly so we can improve teh coverage?
    # TODO(skreft): check that the first file has more than 1 error, check that the second file has 1 new error, check also the lines that changed
    def assert_linter_works(self, linter_name, extensions):
        for extension in extensions:
            data_dirname = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
            filename_repo = os.path.join(self.temp_directory, '%s%s' % (linter_name, extension))
            filename_original = os.path.join(data_dirname, '%s_original%s' % (linter_name, extension))
            filename_error = os.path.join(data_dirname, '%s_error%s' % (linter_name, extension))
            filename_nonewerror = os.path.join(data_dirname, '%s_nonewerror%s' % (linter_name, extension))
            self.assertTrue(os.path.exists(filename_original), 'You must define file "%s"' % filename_original)
            self.assertTrue(os.path.exists(filename_error), 'You must define file "%s"' % filename_error)
            self.assertTrue(os.path.exists(filename_nonewerror), 'You must define file "%s"' % filename_nonewerror)
            shutil.copy(filename_original, filename_repo)
            subprocess.check_output(['git', 'add', filename_repo], stderr=subprocess.STDOUT)
            subprocess.check_output(['git', 'commit', '-m', 'Commit 1'], stderr=subprocess.STDOUT)
            shutil.copy(filename_error, filename_repo)
            try:
                output = subprocess.check_output(['git', 'lint'], stderr=subprocess.STDOUT)
                self.fail('Git lint for file %s should have failed. \n Output:\n%s' %(filename_error, output))
            except subprocess.CalledProcessError as error:
                pass

            subprocess.check_output(['git', 'add', filename_repo], stderr=subprocess.STDOUT)
            subprocess.check_output(['git', 'commit', '-m', 'Commit 2'], stderr=subprocess.STDOUT)
            shutil.copy(filename_nonewerror, filename_repo)
            try:
                subprocess.check_output(['git', 'lint'])
            except subprocess.CalledProcessError as error:
                self.fail('Git lint for file %s should have not failed. \n Output:\n%s' %(filename_nonewerror, error.output))
            subprocess.check_output(['git', 'add', filename_repo], stderr=subprocess.STDOUT)
            subprocess.check_output(['git', 'commit', '-m', 'Commit 3'], stderr=subprocess.STDOUT)
