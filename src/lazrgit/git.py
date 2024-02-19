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


gitctx = GitContext()


def get_recent_messages(max_count: int = 10) -> Generator[str, None, None]:
    """Return the most recent git log messages"""
    already_seen = set()
    branch = gitctx.repo.active_branch.name
    for commit in gitctx.repo.iter_commits(branch, max_count=max_count):
        message = commit.message
        if not message:
            continue
        yield message
