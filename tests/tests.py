#!/usr/bin/env python
from subprocess import Popen, PIPE
import ConfigParser
import os
import re
import sys
import unittest

config = ConfigParser.ConfigParser()
config.read('tests.cfg')


class BaseTest(unittest.TestCase):

    commands = ['../bin/vcprompt', '--without-environment']

    def config(self, field):
        """
        Returns the value for the given ``field`` from the
        configuration file.
        """
        return config.get(self.__class__.__name__.lower(), field)

    def get_repository(self):
        """
        Returns the full path to the repository on disk.
        """
        location = os.path.abspath(__file__).rsplit('/', 1)[0]
        location = os.path.join(location, 'repositories/')
        location = os.path.join(location, self.repository)
        return location

    def revert(self):
        """
        Reverts the repository back to it's original state.
        """
        command = 'cd %s && %s' % (self.get_repository(),
                                   self.revert_command)
        Popen(command, stdout=PIPE, stderr=PIPE, shell=True)

    def touch(self, file):
        """
        Creates a new file.
        """
        f = open(file, 'w')

    def unknown(self):
        """
        Returns the default 'unknown' value from vcprompt.
        """
        commands = self.commands + ['--values', 'UNKNOWN']
        process = Popen(commands, stdout=PIPE)
        output = process.communicate()[0].strip()
        return output

    def vcprompt(self, environment=False, *args, **kwargs):
        """
        A convenience method for forking out to vcprompt.

        Keyword arguments are treated as option/value pairs to be passed
        to vcprompt.

        Returns the output from the call to vcprompt.
        """
        commands = self.commands + ['--path', self.get_repository()]
        for key, value in kwargs.items():
            key = key.replace('_', '-')
            commands.append("--%s" % key)
            commands.append(value)
        process = Popen(commands, stdout=PIPE)
        return process.communicate()[0].strip()


class Base(object):

    def test_depth(self, path='foo/bar/baz', depth='0', format='%s'):
        """
        Tests that vcprompt still works multiple directories deep.
        """
        path = os.path.join(self.get_repository(), path)
        output = self.vcprompt(path=path, max_depth=depth, format=format)
        self.assertEquals(output, self.get_repository().rsplit('/')[-1])

    def test_depth_limited(self, path='foo/bar/baz', depth='2'):
        """
        Tests that the 'depth' argument is followed correctly.
        """
        path = os.path.join(self.get_repository(), path)
        output = self.vcprompt(path=path, max_depth=depth)
        self.assertEquals(output, '')

    def test_format_all(self, string='%s:%n:%r:%h:%b'):
        """
        Tests that all formatting arguments are working correctly.
        """
        output = self.vcprompt(format=string)
        expected = ':'.join([self.config('system'),
                             self.config('system'),
                             self.config('revision'),
                             self.config('hash'),
                             self.config('branch')])
        self.assertEquals(output, expected)

    def test_format_branch(self, string='%b'):
        """
        Tests that the correct branch name is returned.
        """
        output = self.vcprompt(format=string)
        self.assertEquals(output, self.config('branch'))

    def test_format_revision(self, string='%r'):
        """
        Tests that the correct revision ID or hash is returned.
        """
        output = self.vcprompt(format=string)
        self.assertEquals(output, self.config('revision'))

    def test_format_hash(self, string='%h'):
        """
        Tests that the correct hash or revision ID is returned.
        """
        self.assertEquals(self.vcprompt(format=string),
                          self.config('hash'))

    def test_format_modified(self, string='%m'):
        """
        Tests for modified files in the repository.
        """
        output = self.vcprompt(format=string)
        self.assertEquals(output, '')

        f = open(os.path.join(self.get_repository(), 'quotes.txt'), 'w')
        f.write('foo')

        output = self.vcprompt(format=string)
        self.assertEquals(output, '+')

        self.revert()

        output = self.vcprompt(format=string)
        self.assertEquals(output, '')

    def test_format_system(self, string='%s'):
        """
        Tests that the '%s' argument correctly returns the system name.
        """
        output = self.vcprompt(format=string)
        self.assertEquals(output, self.config('system'))

    def test_format_system_alt(self, string='%n'):
        """
        Tests that the '%m' argument correctly returns the system name.
        """
        return self.test_format_system(string=string)

    def test_format_untracked_files(self, string="%u"):
        """
        Tests for any untracked files in the repository.
        """
        output = self.vcprompt(format=string)
        self.assertEquals(output, '')

        file = os.path.join(self.get_repository(), 'untracked_file')
        self.touch(file)

        output = self.vcprompt(format=string)
        self.assertEquals(output, '?')

        os.remove(file)

        output = self.vcprompt(format=string)
        self.assertEquals(output, '')


class Bazaar(Base, BaseTest):

    revert_command = 'bzr revert --no-backup'
    repository = 'bzr'


class Darcs(Base, BaseTest):

    revert_command = 'darcs revert -a'
    repository = 'darcs'


class Fossil(Base, BaseTest):

    revert_command = 'fossil revert'
    repository = 'fossil'


class Git(Base, BaseTest):

    revert_command = 'git reset -q --hard HEAD'
    repository = 'git'


class Mercurial(Base, BaseTest):

    revert_command = 'hg revert -a --no-backup'
    repository = 'hg'


class Subversion(Base, BaseTest):

    revert_command = 'svn revert -R .'
    repository = 'svn'

    def test_depth_limited(self):
        """
        SVN puts '.svn' directories everywhere, so the limited depth test
        doesn't apply here.
        """
        return self.test_depth()

if __name__ == '__main__':
    unittest.main()
