#!/usr/bin/env python3

from textual import on, work
from textual.events import Mount
from textual.app import App, ComposeResult
from textual.screen import ModalScreen, Screen
from textual.containers import Container, VerticalScroll, Grid
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Static, SelectionList, TextArea, RadioSet, Button, Label
from git import Repo
from typing import Generator, Optional
import re
from . import jira


#class ConfirmCommitModal(ModalScreen[bool]):
class ConfirmCommitModal(Screen[bool]):
    """Ask the user if they want to commit and exit"""

    def compose(self) -> ComposeResult:
        yield Label("Are you sure you want to commit?", id="question")
        yield Button("Yes", variant="success", id="yes")
        yield Button("Cancel", variant="primary", id="cancel")

    @on(Button.Pressed, "#yes")
    def handle_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        self.dismiss(False)


class GitBrowser(App):
    BINDINGS = [
            ("c", "commit", "Commit"),
            ("q", "quit", "Quit"),
        ]
    DEFAULT_CSS = """
    ConfirmCommitModal {
        layout: grid;
        grid-size: 2 2;                
        align: center middle;
    }

    ConfirmCommitModal > Label {
        margin: 1;       
        text-align: center;
        column-span: 2;    
        width: 1fr;
    }

    ConfirmCommitModal Button {
        margin: 2; 
        width: 1fr;     
    }

    Screen {
        background: $surface-darken-1;
    }

    #tree-view {
        display: none;
        scrollbar-gutter: stable;
        overflow: auto;
        width: auto;
        height: 100%;
        dock: left;
    }

    #file-list {
        max-height: 50%;
    }
    #commit-message {
        min-height: 5;
    }
    """

    def get_changed_files(self) -> Generator[tuple[str, str, bool], None, None]:
        repo = Repo('.')
        already_seen = set()

        #  unstaged files
        for file in [file.a_path for file in repo.index.diff(None)]:
            yield((file, file, False))
            already_seen.add(file)
        #  staged files
        for file in [file.a_path for file in repo.index.diff(repo.head.commit)]:
            if file in already_seen:
                continue
            yield((file, file, True))


    def get_untracked_files(self) -> Generator[tuple[str, str, bool], None, None]:
        repo = Repo('.')
        for file in repo.untracked_files:
            yield((f'[UNTRACKED] {file}', file, False))


    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        with Container():
            repo = Repo(".")
            branch = str(repo.active_branch)
            branch_style = {
                    'master': '[white]',
                    'stg': ':warning: [yellow]',
                    'prod': ':warning: [red]',
                    }.get(branch, "[green]")

            import syslog
            syslog.syslog(f"@@@ Branch: [{branch_style}]{branch}[/]")
            yield Label(f"Branch: {branch_style}{branch}[/]", id='branch', classes="red")
            yield SelectionList[str](
                    *(list(sorted(self.get_changed_files())) + list(self.get_untracked_files())),
                    id='file-list',
                    )
            yield RadioSet(*jira.get_cases(), id='cases')
            yield TextArea(name='Commit Message', id='commit-message')
        #with Container():
        #    yield DirectoryTree(path, id="tree-view")
        #    with VerticalScroll(id="code-view"):
        #        yield Static(id="code", expand=True)
        yield Footer()


    def on_mount(self) -> None:
        self.query_one(SelectionList).border_title = "Files"
        self.query_one(RadioSet).border_title = "Cases"
        self.query_one(TextArea).border_title = "Commit Message"


    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def update_selected_view(self) -> None:
        selected = self.query_one(SelectionList).selected

        repo = Repo(".")
        unstaged_files = list([file.a_path for file in repo.index.diff(None)])
        staged_files = list([file.a_path for file in repo.index.diff(repo.head.commit)])

        repo.index.add(selected)

        for file in staged_files:
            if file not in selected and file not in unstaged_files:
                repo.index.remove([file])


    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        current_text = self.query_one("#commit-message").text
        m = re.match(r'^RG-[0-9]+:?\s+(.*)', current_text)
        if m:
            current_text = m.group(1)

        case = str(event.pressed.label)
        case = case.split()[0]

        current_text = case + ' ' + current_text
        self.query_one("#commit-message").text = current_text

    @work
    async def action_commit(self) -> None:
        if await self.push_screen_wait(ConfirmCommitModal()):
            repo = Repo('.')
            commit_message = self.query_one("#commit-message").text
            repo.index.commit(commit_message)
            self.app.exit()
        self.refresh()

def main():
    GitBrowser().run()

if __name__ == "__main__":
    main()