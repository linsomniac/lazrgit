#!/usr/bin/env python3

from textual import on, work
from textual.events import Mount, DescendantFocus
from textual.app import App, ComposeResult
from textual.screen import ModalScreen, Screen
from textual.containers import Container, VerticalScroll, Grid
from textual.reactive import var
from textual.widgets import (
    DirectoryTree,
    Footer,
    Header,
    Static,
    SelectionList,
    TextArea,
    RadioSet,
    Button,
    Label,
    RadioButton,
)
from rich.syntax import Syntax
from typing import Generator, Optional
import re
from . import jira
from . import git
from . import ask_openai
import asyncio
from concurrent.futures import ThreadPoolExecutor


repo = git.gitctx.repo


def all_changed_files() -> Generator[tuple[str, str, bool], None, None]:
    already_seen = set()

    #  unstaged files
    for file in [file.a_path for file in repo.index.diff(None)]:
        yield ((file, file, False))
        already_seen.add(file)
    #  staged files
    for file in [file.a_path for file in repo.index.diff(repo.head.commit)]:
        if file in already_seen:
            continue
        yield ((file, file, True))


def label_untracked_files() -> Generator[tuple[str, str, bool], None, None]:
    for file in repo.untracked_files:
        yield ((f"[UNTRACKED] {file}", file, False))


class FileDiffModal(Screen[str]):
    """Display the diff of a file"""

    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    FileDiffModal {
        align: center middle;
    }

    FileDiffModal > Label {
        max-height: 1;
        text-align: center;
        width: 1fr;
    }

    FileDiffModal > VerticalScroll {
        max-height: 100%;
        text-align: center;
        width: 1fr;
    }

    Screen {
        background: $surface-darken-1;
    }
    """

    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename

    def compose(self) -> ComposeResult:
        yield Label(f"Diff for {self.filename}", id="title")
        diff = git.get_file_diff(self.filename)
        syntax = Syntax(diff, "diff", line_numbers=True)
        yield VerticalScroll(Static(syntax))


    def action_cancel(self) -> None:
        self.dismiss()


class ConfirmCommitModal(Screen[str]):
    """Ask the user if they want to commit and exit"""

    BINDINGS = [
        ("c", "commit", "Commit only"),
        ("p", "commitpush", "commit and Push"),
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    ConfirmCommitModal {
        layout: grid;
        grid-size: 1 2;                
        align: center middle;
    }

    ConfirmCommitModal Button {
        margin: 2; 
        width: 1fr;     
    }

    Screen {
        background: $surface-darken-1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Are you sure you want to commit?", id="question")
        with Container():
            yield Button("C)ommit only", variant="success", id="commit")
            yield Button("commit and P)ush", variant="success", id="commit-push")
            yield Button("Cancel (ESC)", variant="primary", id="cancel")

    @on(Button.Pressed, "#commit-push")
    def handle_commitpush(self) -> None:
        with open("log", "a") as f:
            f.write("1\n")
        self.dismiss("commit push")

    def action_commitpush(self) -> None:
        with open("log", "a") as f:
            f.write("2\n")
        self.dismiss("commit push")

    @on(Button.Pressed, "#commit")
    def handle_commit(self) -> None:
        with open("log", "a") as f:
            f.write("3\n")
        self.dismiss("commit only")

    def action_commit(self) -> None:
        with open("log", "a") as f:
            f.write("4\n")
        self.dismiss("commit only")

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        with open("log", "a") as f:
            f.write("5\n")
        self.dismiss("cancel")


    def action_cancel(self) -> None:
        with open("log", "a") as f:
            f.write("6\n")
        self.dismiss("cancel")


class GitBrowser(App):
    BINDINGS = [
        ("c,ctrl+c", "commit", "Commit"),
        ("q", "quit", "Quit"),
        ("ctrl+d,d", "show_diff", "Show Diff"),
        ("ctrl+g,g", "generate_message", "Generate Message"),
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

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        with Container(id="main"):
            branch = repo.active_branch.name
            branch_style = {
                "main": "[white]",
                "master": "[white]",
                "stg": ":warning: [yellow]",
                "prod": ":warning: [red]",
            }.get(branch, "[green]")

            yield Label(
                f"Branch: {branch_style}{branch}[/]", id="branch", classes="red"
            )
            yield SelectionList[str](
                *(list(sorted(all_changed_files())) + list(label_untracked_files())),
                id="file-list",
            )

            def get_cases():
                self.lzr_tickets = set()
                for ticket_id, ticket_desc in jira.get_cases():
                    self.lzr_tickets.add(ticket_id)
                    yield RadioButton(
                        f"{ticket_id} {ticket_desc}",
                        id=ticket_id,
                        classes="case-button",
                    )

            yield RadioSet(*get_cases(), id="cases")
            yield TextArea(name="Commit Message", id="commit-message")
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one(SelectionList).border_title = "Files"
        self.query_one(RadioSet).border_title = "Cases"
        self.query_one(TextArea).border_title = "Commit Message"

        # self.my_task = asyncio.create_task(self.load_cases())

    async def load_cases(self) -> None:
        def make_buttons(cases):
            self.lzr_tickets = set()
            for ticket_id, ticket_desc in cases:
                self.lzr_tickets.add(ticket_id)
                yield RadioButton(
                    f"{ticket_id} {ticket_desc}",
                    id=ticket_id,
                    classes="case-button",
                )

        self.cases = jira.get_cases()
        for button in make_buttons(self.cases):
            yield button

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def update_files(self) -> None:
        selected = self.query_one(SelectionList).selected

        unstaged_files = list([file.a_path for file in repo.index.diff(None)])
        staged_files = list([file.a_path for file in repo.index.diff(repo.head.commit)])

        repo.index.add(selected)

        for file in staged_files:
            if file not in selected and file not in unstaged_files:
                repo.git.reset(file)

    @on(DescendantFocus, "#cases")
    def on_cases_focused(self, _) -> None:
        #  skip if any cases are activated
        for radio in self.query(".case-button"):
            if radio.value:
                return

        #  look for a recent matching ticket
        for message in git.get_recent_messages():
            for ticket_id in self.lzr_tickets:
                if ticket_id in message:
                    self.query_one(f"#{ticket_id}").toggle()
                    return

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        current_text = self.query_one("#commit-message").text
        m = re.match(r"^RG-[0-9]+:?\s+(.*)", current_text)
        if m:
            current_text = m.group(1)

        case = str(event.pressed.label)
        case = case.split()[0]

        current_text = case + " " + current_text
        self.query_one("#commit-message").text = current_text

    @work
    async def action_commit(self) -> None:
        if not self.query_one(SelectionList).selected:
            self.notify("No files are selected for committing!", title="Can't Commit")
            return

        commit_message = self.query_one("#commit-message").text
        if not commit_message:
            self.notify("No commit message entered.", title="Can't Commit")
            return

        ret = await self.push_screen_wait(ConfirmCommitModal())
        if ret != "cancel":
            commit_message = self.query_one("#commit-message").text
            repo.index.commit(commit_message)
        if ret == "commit push":
            repo.git.pull()
            repo.git.push()
        if ret != "cancel":
            self.app.exit()
        self.refresh()

    @work
    async def action_show_diff(self) -> None:
        highlighted_index = self.query_one(SelectionList).highlighted
        if highlighted_index is None:
            self.notify("No files are selected for diff!", title="Can't Diff")
            return

        highlighted_filename = (
            self.query_one(SelectionList).get_option_at_index(highlighted_index).value
        )
        await self.push_screen_wait(FileDiffModal(highlighted_filename))
        self.refresh()

    @work
    async def action_generate_message(self) -> None:
        current_text = self.query_one("#commit-message").text

        selected_files = self.query_one(SelectionList).selected
        if not selected_files:
            self.notify("No files have been selected", title="File Selection Error")
            return

        ticket_number = None
        current_message = None
        m = re.match(r"^(RG-[0-9]+)(:?\s+(.*))?", current_text)
        if m:
            ticket_number = m.group(1)
            current_message = m.group(3).strip()

        system_message = """You are an expert in computer source code documentation.  I
                will provide you with a a set of files and their unified diffs of changes
                I have made.  I will also provide a ticket number and a brief description
                of the ticket.  I would like you to write a commit message for me.  The
                commit message should be follow best practices for a git commit message:
                a concise but descriptive first line that summarizes the changes, a blank
                line, and then more detailed information about the changes if necessary
                to expand on the summary line.  You will *ONLY* output the the change
                message, any discussion about the changes *MUST* be prefixed with the
                "#" comment character.  If you need more information, please ask me.
                If you write a perfect change message, I will give you a $500 bonus.
                The current commit message, if provided, should be used as the basis
                for your new commit message, but you should feel free to modify it as
                you see fit to make it more clear and easily understood.
                """
        user_message = ""
        if ticket_number:
            user_message += f"The current ticket number is {ticket_number} and this *MUST* be included at the beginning of the commit summary.  "
            ticket_description = str(self.query_one(f"#{ticket_number}").label).split(None, 1)[1]
            user_message += f"A brief summary of the ticket that this commit is for is: '{ticket_description}'.  "
        if current_message:
            user_message += ("The current commit message I have written, which I would "
                "like you to use as the basis for your new commit message, but "
                f"optimized for carity and readability, is:\n\n```\n{current_message}\n```")
        for filename in selected_files:
            diff = git.get_file_diff(filename)
            user_message += f"\n\nUnified diff of changes for file '{filename}':\n{diff}\n\n"

        ret = ask_openai.ask_openai(system_message, user_message)
        self.query_one("#commit-message").text = ret
        
        
def main():
    GitBrowser().run()


if __name__ == "__main__":
    main()
