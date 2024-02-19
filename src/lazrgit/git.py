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


def get_recent_cases(max_count: int=10) -> Generator[str, None, None]:
    '''Return the most recent case numbers'''
    already_seen = set()
    branch = git.repo.active_branch.name
    for commit in git.repo.iter_comments(branch, max_count):
        case = commit.message.split()[0]
        case = case.rstrip(":")
        if case in already_seen:
            continue
        already_seen.add(case)
        yield case
