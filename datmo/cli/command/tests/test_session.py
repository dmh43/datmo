"""
Tests for SessionCommand
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import glob
import tempfile
import platform
from argparse import ArgumentError
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

from datmo.config import Config
from datmo.cli.driver.helper import Helper
from datmo.cli.command.session import SessionCommand
from datmo.cli.command.project import ProjectCommand


class TestSessionCommand():
    def setup_method(self):
        # provide mountable tmp directory for docker
        tempfile.tempdir = "/tmp" if not platform.system(
        ) == "Windows" else None
        test_datmo_dir = os.environ.get('TEST_DATMO_DIR',
                                        tempfile.gettempdir())
        self.temp_dir = tempfile.mkdtemp(dir=test_datmo_dir)
        Config().set_home(self.temp_dir)
        self.cli_helper = Helper()

    def teardown_method(self):
        pass

    def __set_variables(self):
        self.project_command = ProjectCommand(self.cli_helper)
        self.project_command.parse(
            ["init", "--name", "foobar", "--description", "test model"])

        @self.project_command.cli_helper.input("\n")
        def dummy(self):
            return self.project_command.execute()

        dummy(self)
        self.session_command = SessionCommand(self.cli_helper)

    def test_session_no_subcommand(self):
        self.__set_variables()
        self.session_command.parse(["session"])
        assert self.session_command.execute()

    def test_session_create(self):
        self.__set_variables()
        self.session_command.parse(["session", "create", "--name", "pizza"])
        result = self.session_command.execute()
        assert result
        return result

    def test_session_select(self):
        session_obj = self.test_session_create()
        # Test successful select name
        self.session_command.parse(["session", "select", "pizza"])
        assert self.session_command.execute()
        current = 0
        for s in self.session_command.session_controller.list():
            print("%s - %s" % (s.name, s.current))
            if s.current == True:
                current = current + 1
        assert current == 1
        # Reset to default
        self.session_command.parse(["session", "select", "default"])
        # Test successful select id
        self.session_command.parse(["session", "select", session_obj.id])
        assert self.session_command.execute()
        current = 0
        for s in self.session_command.session_controller.list():
            print("%s - %s" % (s.name, s.current))
            if s.current == True:
                current = current + 1
        assert current == 1

    def test_session_ls(self):
        created_session_obj = self.test_session_create()

        # Test success (defaults)
        self.session_command.parse(["session", "ls"])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs

        # Test failure (format)
        failed = False
        try:
            self.session_command.parse(["session", "ls", "--format"])
        except ArgumentError:
            failed = True
        assert failed

        # Test success format csv
        self.session_command.parse(["session", "ls", "--format", "csv"])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs

        # Test success format csv, download default
        self.session_command.parse(
            ["session", "ls", "--format", "csv", "--download"])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs
        test_wildcard = os.path.join(
            self.session_command.session_controller.home, "session_ls_*")
        paths = [n for n in glob.glob(test_wildcard) if os.path.isfile(n)]
        assert paths
        assert open(paths[0], "r").read()
        os.remove(paths[0])

        # Test success format csv, download exact path
        test_path = os.path.join(self.temp_dir, "my_output")
        self.session_command.parse([
            "session", "ls", "--format", "csv", "--download",
            "--download-path", test_path
        ])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs
        assert os.path.isfile(test_path)
        assert open(test_path, "r").read()
        os.remove(test_path)

        # Test success format table
        self.session_command.parse(["session", "ls"])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs

        # Test success format table, download default
        self.session_command.parse(["session", "ls", "--download"])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs
        test_wildcard = os.path.join(
            self.session_command.session_controller.home, "session_ls_*")
        paths = [n for n in glob.glob(test_wildcard) if os.path.isfile(n)]
        assert paths
        assert open(paths[0], "r").read()
        os.remove(paths[0])

        # Test success format table, download exact path
        test_path = os.path.join(self.temp_dir, "my_output")
        self.session_command.parse(
            ["session", "ls", "--download", "--download-path", test_path])
        session_objs = self.session_command.execute()
        assert created_session_obj in session_objs
        assert os.path.isfile(test_path)
        assert open(test_path, "r").read()
        os.remove(test_path)

    def test_session_update(self):
        created_session_obj = self.test_session_create()
        # Test successful update
        updated_name = "new"
        self.session_command.parse([
            "session", "update", created_session_obj.id, "--name", updated_name
        ])
        assert self.session_command.execute()
        # Test failure update
        self.session_command.parse(
            ["session", "update", "random_id", "--name", updated_name])
        assert not self.session_command.execute()
        # Test success nothing given
        self.session_command.parse(
            ["session", "update", created_session_obj.id])
        assert self.session_command.execute()

    def test_session_delete(self):
        self.test_session_create()
        # Test successful delete name
        self.session_command.parse(["session", "delete", "pizza"])
        assert self.session_command.execute()
        # Test failure delete default name
        self.session_command.parse(["session", "delete", "default"])
        assert not self.session_command.execute()
        # Test failure delete random name
        self.session_command.parse(["session", "delete", "random_name"])
        assert not self.session_command.execute()
        session_obj = self.test_session_create()
        # Test successful delete id
        self.session_command.parse(["session", "delete", session_obj.id])
        assert self.session_command.execute()
        # Test failure delete default id
        self.session_command.parse(["session", "ls"])
        session_objs = self.session_command.execute()
        self.session_command.parse(["session", "delete", session_objs[0].id])
        assert not self.session_command.execute()
        # Test failure delete random id
        self.session_command.parse(["session", "delete", "random_id"])
        assert not self.session_command.execute()
