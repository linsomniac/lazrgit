#!/usr/bin/env python

from git import Repo
from typing import Generator
import difflib


class GitContext:
    def __init__(self):
        self.set_repo(".")

    def set_repo(self, path: str) -> None:
        self.repo = Repo(path)


gitctx = GitContext()


def unified_diff(old: str, new: str) -> str:
    """Given two strings, generate a unified diff between them"""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines)
    return ''.join(diff)


def get_recent_messages(max_count: int = 10) -> Generator[tuple[str, list[str]], None, None]:
    """Return the most recent commit messages
    """
    branch = gitctx.repo.active_branch.name
    for commit in gitctx.repo.iter_commits(branch, max_count=max_count):
        message = commit.message
        if not message:
            continue
        yield message


def get_recent_messages_and_diffs(max_count: int = 10) -> Generator[tuple[str, list[str]], None, None]:
    """Return the most recent git log messages and their diffs
    Yields the commit message and a list of diff strings.

    for commit_message, diffs_list in get_recent_messages_and_diffs(max_count):
    """
    branch = gitctx.repo.active_branch.name
    for commit in gitctx.repo.iter_commits(branch, max_count=3):
        message = commit.message
        if not message:
            continue

        diffs = []
        for diff in commit.diff('HEAD~1').iter_change_type('M'):  # 'M' for modified files
            diffs.append(get_context_diff(diff.a_blob.data_stream.read().decode(), diff.b_blob.data_stream.read().decode()))
        yield message, diffs


def get_file_recent_messages_and_diffs(filename: str, max_count: int = 10) -> Generator[tuple[str, list[str]], None, None]:
    """Return the most recent git log messages and their diffs for a specific file
    Yields the commit message and a list of diff strings.

    for commit_message, diffs_list in get_recent_messages_and_diffs(max_count):
    """
    branch = gitctx.repo.active_branch.name
    for commit in gitctx.repo.iter_commits(branch, paths=filename, max_count=3):
        message = commit.message
        if not message:
            continue

        diffs = []
        for diff in commit.diff('HEAD~1').iter_change_type('M'):  # 'M' for modified files
            if diff.a_path != filename:
                continue
            diffs.append(get_context_diff(diff.a_blob.data_stream.read().decode(), diff.b_blob.data_stream.read().decode()))
        yield message, diffs


def get_file_diff(filename: str) -> Generator[tuple[str, list[str]], None, None]:
    """Return the diff of the file's current state and last commit.
    """
    diff = gitctx.repo.git.diff(gitctx.repo.head.commit.tree, filename)
    return diff