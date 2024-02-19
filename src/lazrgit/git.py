#!/usr/bin/env python

import configparser
import os
from git import Repo
from typing import Generator


class GitContext:
    def __init__(self):
        self.set_repo(".")

    def set_repo(self, path: str) -> None:
        self.repo = Repo(path)


git = GitContext()
