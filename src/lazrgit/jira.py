#!/usr/bin/env python3

import argparse
from typing import Union
from jira import JIRA
from . import internal
from typing import Generator


def get_cases() -> Generator[tuple, None, None]:
    token = internal.context.config.get("jira", "token")
    url = internal.context.config.get("jira", "url")
    username = internal.context.config.get("jira", "username")

    jira = JIRA(url, basic_auth=(username, token))

    # Search for issues assigned to the current user
    issues = jira.search_issues(
        "assignee = currentUser() AND resolution = Unresolved AND updated >= -30d ORDER BY updated DESC, created DESC"
    )

    # Print the key and summary of each issue
    for issue in issues:
        yield (issue.key, issue.fields.summary)
