"""
Unit tests for the Deis CLI auth commands.

Run these tests with "python -m unittest client.tests.auth"
or with "./manage.py test client.AuthTest".
"""

from __future__ import unicode_literals
from unittest import TestCase

import pexpect

from client.deis import __version__
from .utils import DEIS
from .utils import DEIS_SERVER
from .utils import setup
from .utils import teardown


class AuthTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.username, cls.password, _ = setup()

    @classmethod
    def tearDownClass(cls):
        teardown(cls.username, cls.password, None)

    def test_login(self):
        # log in the interactive way
        child = pexpect.spawn("{} login {}".format(DEIS, DEIS_SERVER))
        child.expect('username: ')
        child.sendline(self.username)
        child.expect('password: ')
        child.sendline(self.password)
        child.expect("Logged in as {}".format(self.username))
        child.expect(pexpect.EOF)

    def test_logout(self):
        child = pexpect.spawn("{} logout".format(DEIS))
        child.expect('Logged out')
        # log in the one-liner way
        child = pexpect.spawn("{} login {} --username={} --password={}".format(
            DEIS, DEIS_SERVER, self.username, self.password))
        child.expect("Logged in as {}".format(self.username))
        child.expect(pexpect.EOF)


class HelpTest(TestCase):
    """Test that the client can document its own behavior."""

    def test_deis(self):
        """Test that the `deis` command on its own returns usage."""
        child = pexpect.spawn(DEIS)
        child.expect('Usage: deis <command> \[--formation <formation>\] \[<args>...\]')

    def test_help(self):
        """Test that the client reports its help message."""
        child = pexpect.spawn('{} --help'.format(DEIS))
        child.expect('This Deis command-line client.*to a formation\.')
        child = pexpect.spawn('{} -h'.format(DEIS))
        child.expect('This Deis command-line client.*to a formation\.')
        child = pexpect.spawn('{} help'.format(DEIS))
        child.expect('This Deis command-line client.*to a formation\.')


class VersionTest(TestCase):
    """Test that the client can report its version string."""

    def test_version(self):
        """Test that the client reports its version string."""
        child = pexpect.spawn('{} --version'.format(DEIS))
        child.expect("Deis CLI {}".format(__version__))
