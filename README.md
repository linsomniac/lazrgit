# lazrgit

A TUI front-end for doing git commits that is oriented specifically towards my workflow.

## Overview

This TUI is specifically for users who use git with Jira and tag their commits with Jira
case numbers.  It will display a list of files you may wish to stage, a list of Jira
cases, and an edit box for making your commit message.

Future updates might include ability to query tickets from other sources (github, ...?)
and showing a diff of selected files.

## Motivation

I have a bad habit of working on one set of changes and then doing another set of changes
and doing a "git commit -a -m ..." which commits files from both the tasks I'm working on.
Since this displays a file chooser, it makes it more obvious what I'm committing before I
do so.  The display of open cases assigned to me makes it easier to pick the case to
assign the changes to.

[//]: # ( vim: set tw=90 ts=4 sw=4 ai: )
