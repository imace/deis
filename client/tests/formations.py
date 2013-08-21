"""
Unit tests for the Deis CLI formations commands.

Run these tests with "python -m unittest client.tests.formations"
or with "./manage.py test client.FormationsTest".
"""

from __future__ import unicode_literals
from unittest import TestCase

import pexpect

from .utils import DEIS
from .utils import random_repo
from .utils import setup
from .utils import teardown


class FormationsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        repo_name, repo_url = random_repo()
        cls.username, cls.password, cls.repo_dir = setup(repo_url)

    @classmethod
    def tearDownClass(cls):
        teardown(cls.username, cls.password, cls.repo_dir)

    def test_create(self):
        child = pexpect.spawn("python {} create --flavor=ec2-us-west-2".format(DEIS))
        child.expect('created (?P<name>[a-z]{6}-[a-z]{8}).*to scale a basic formation')
        formation = child.match.group('name')
        # destroy formation the one-liner way
        child = pexpect.spawn("{} destroy --confirm={}".format(DEIS, formation))
        child.expect('Git remote deis removed')
        child.expect(pexpect.EOF)

    def test_destroy(self):
        child = pexpect.spawn("{} create --flavor=ec2-us-west-2".format(DEIS))
        child.expect('created (?P<name>[a-z]{6}-[a-z]{8}).*to scale a basic formation')
        formation = child.match.group('name')
        # destroy formation the interactive way
        child = pexpect.spawn("{} destroy".format(DEIS))
        child.expect('> ')
        child.sendline(formation)
        child.expect('Git remote deis removed')
        child.expect(pexpect.EOF)
