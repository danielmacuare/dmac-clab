"""
Network automation CLI for configuration management.

This module provides a command-line interface for the py_netauto package,
enabling users to render, validate, and deploy device configurations
with sophisticated filtering capabilities.

"""

import typer

from py_netauto.cli.commands.push import push_command
from py_netauto.cli.commands.render import render_command
from py_netauto.cli.commands.sessions import sessions_abort_command, sessions_list_command

# Create main Typer application
app = typer.Typer(
    name="py-netauto",
    help="Network automation CLI for configuration management",
    add_completion=False,
    no_args_is_help=True,
)

# Register render command
app.command(name="render", help="Render device configurations from Jinja2 templates")(render_command)

# Register push command
app.command(name="push", help="Push configurations to network devices (dry-run by default)")(push_command)

# Create sessions subcommand group
sessions_app = typer.Typer(
    name="sessions",
    help="Manage configuration sessions on devices",
    no_args_is_help=True,
)

# Register sessions list command
sessions_app.command(name="list", help="List all configuration sessions on devices")(sessions_list_command)

# Register sessions abort command
sessions_app.command(name="abort", help="Abort all pending configuration sessions")(sessions_abort_command)

# Add sessions subcommand group to main app
app.add_typer(sessions_app, name="sessions")


if __name__ == "__main__":
    app()
