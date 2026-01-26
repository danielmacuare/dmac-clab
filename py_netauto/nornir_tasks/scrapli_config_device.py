from pathlib import Path

from nornir.core import Nornir
from nornir.core.task import AggregatedResult, Result, Task
from nornir_rich.functions import print_result
from nornir_scrapli.tasks import cfg_abort_config, cfg_commit_config, cfg_diff_config, cfg_load_config, send_command

from py_netauto.config import GENERATED_CONFIGS_FOLDER_PATH
from py_netauto.utils.nornir_helpers import initialize_nornir


def list_all_sessions(task: Task) -> Result:
    """
    List all configuration sessions on a device.

    This task queries the device for active configuration sessions and returns
    information about each session.

    **Currently only supports Arista EOS devices.**

    Args:
        task: Nornir task object containing host information.

    Returns:
        Result object containing session information as a dictionary with:
            - sessions: List of session dictionaries with session details
            - count: Number of active sessions
            - raw_output: Raw command output from the device

    Raises:
        ValueError: If the device platform is not supported.
        Exception: If session detection commands fail.

    Example:
        Basic usage:

        ```python
        result = nr.run(task=list_all_sessions)
        for host, multi_result in result.items():
            sessions_info = multi_result[0].result
            print(f"{host}: {sessions_info['count']} sessions")
        ```

    Note:
        Platform-specific behavior:
        - Arista EOS: Uses 'show configuration sessions' command

    """
    platform = task.host.platform

    # Currently only Arista EOS is supported
    if platform == "arista_eos":
        return _list_arista_sessions(task)

    msg = f"Platform '{platform}' not supported for session listing. Currently only 'arista_eos' is supported."
    raise ValueError(msg)


def _list_arista_sessions(task: Task) -> Result:
    """
    List configuration sessions on Arista EOS devices.

    Parses the output of 'show configuration sessions' to extract active session
    information. The parser correctly handles the table format and skips
    configuration lines (Maximum, Merge, Autosave).

    Args:
        task: Nornir task object containing host information.

    Returns:
        Result with session information including session name, status, and details.

    """
    # Execute the command to get session information
    response = task.run(task=send_command, command="show configuration sessions")
    output = response.result

    sessions = []
    in_session_table = False

    for line in output.splitlines():
        line_stripped = line.strip()

        # Skip empty lines
        if not line_stripped:
            continue

        # Skip configuration lines (Maximum, Merge, Autosave)
        if any(keyword in line for keyword in ["Maximum", "Merge", "Autosave"]):
            continue

        # Check for header line
        if "Name" in line and "State" in line:
            continue

        # Check for separator line (dashes)
        if line_stripped.startswith("---"):
            in_session_table = True
            continue

        # Only parse lines after the separator that have actual session data
        if in_session_table and line_stripped:
            parts = line.split()
            # Valid session lines should have at least 2 parts (name and state)
            if len(parts) >= 2:
                session_name = parts[0]
                session_state = parts[1]

                session_info = {
                    "name": session_name,
                    "status": session_state.lower(),
                    "details": line.strip(),
                }
                sessions.append(session_info)

    return Result(
        host=task.host,
        result={
            "sessions": sessions,
            "count": len(sessions),
            "raw_output": output,
        },
    )


def abort_all_sessions(task: Task) -> Result:
    """
    Detect and abort all pending configuration sessions on a device.

    This task queries the device for active configuration sessions and aborts
    each one. It is useful for cleaning up stale sessions left by failed operations.

    **Currently only supports Arista EOS devices.**

    Args:
        task: Nornir task object containing host information.

    Returns:
        Result object containing the number of sessions aborted.

    Raises:
        ValueError: If the device platform is not supported.
        Exception: If session detection or abort commands fail.

    Example:
        Basic usage:

        ```python
        result = nr.run(task=abort_all_sessions)
        for host, multi_result in result.items():
            abort_info = multi_result[0].result
            print(f"{host}: Aborted {abort_info['aborted_count']} sessions")
        ```

    Note:
        Platform-specific behavior:
        - Arista EOS: Uses 'show configuration sessions' and 'configure session <name>; abort'

    """
    platform = task.host.platform

    # Currently only Arista EOS is supported
    if platform == "arista_eos":
        return _abort_arista_sessions(task)

    msg = f"Platform '{platform}' not supported for session abort. Currently only 'arista_eos' is supported."
    raise ValueError(msg)


def abort_specific_session(task: Task, session_name: str) -> None:
    """
    Abort a specific configuration session on a device.

    This task aborts a single named configuration session on the device.

    **Currently only supports Arista EOS devices.**

    Args:
        task: Nornir task object containing host information.
        session_name: Name of the session to abort.

    Returns:
        None. The task aborts the specified session on the device.

    Raises:
        ValueError: If the device platform is not supported.
        Exception: If session abort commands fail.

    Example:
        Basic usage:

        ```python
        nr.run(task=abort_specific_session, session_name="DMAC-L1")
        ```

    Note:
        Platform-specific behavior:
        - Arista EOS: Uses 'configure session <name>; abort'

    """
    platform = task.host.platform

    # Currently only Arista EOS is supported
    if platform == "arista_eos":
        _abort_arista_specific_session(task, session_name)
    else:
        msg = f"Platform '{platform}' not supported for session abort. Currently only 'arista_eos' is supported."
        raise ValueError(msg)


def _abort_arista_specific_session(task: Task, session_name: str) -> None:
    """
    Abort a specific configuration session on Arista EOS devices.

    Enters the specified configuration session and aborts it, discarding any
    uncommitted changes.

    Args:
        task: Nornir task object containing host information.
        session_name: Name of the session to abort.

    """
    # Enter the session and abort it
    task.run(task=send_command, command=f"configure session {session_name}")
    task.run(task=send_command, command="abort")
    print(f"[INFO] - Aborted session: {session_name} on {task.host.name}")


def _abort_arista_sessions(task: Task) -> Result:
    """
    Abort all configuration sessions on Arista EOS devices.

    This function first lists all active sessions using the same parsing logic
    as list_all_sessions, then aborts each session found. This ensures consistent
    parsing and avoids code duplication.

    Args:
        task: Nornir task object containing host information.

    Returns:
        Result object containing:
            - aborted_count: Number of sessions aborted
            - sessions: List of session dictionaries that were aborted

    """
    # Reuse the list_all_sessions logic to get parsed sessions
    sessions_result = _list_arista_sessions(task)
    sessions_info = sessions_result.result

    aborted_count = 0
    # Abort each session found
    for session in sessions_info["sessions"]:
        session_name = session["name"]
        task.run(task=send_command, command=f"configure session {session_name}")
        task.run(task=send_command, command="abort")
        print(f"[INFO] - Aborted session: {session_name} on {task.host.name}")
        aborted_count += 1

    return Result(
        host=task.host,
        result={"aborted_count": aborted_count, "sessions": sessions_info["sessions"]},
    )


def config_device_dry_run(task: Task, config_dir: Path | None = None) -> Result:
    """
    Load configuration and retrieve diff without committing changes.

    This task performs a dry-run configuration operation by loading the
    configuration to a device session, retrieving the diff, and then aborting
    the session without committing. This allows previewing changes before
    applying them.

    Args:
        task: Nornir task object containing host information.
        config_dir: Optional path to directory containing configuration files.
            If not provided, uses GENERATED_CONFIGS_FOLDER_PATH from environment.

    Returns:
        Result object containing the configuration diff as a string.

    Raises:
        FileNotFoundError: If the configuration file for the device is not found.
        Exception: If configuration loading or diff retrieval fails.

    Example:
        Basic usage with defaults:

        ```python
        result = nr.run(task=config_device_dry_run)
        for host, multi_result in result.items():
            print(f"Diff for {host}:")
            print(multi_result[0].result)
        ```

        With custom config directory:

        ```python
        result = nr.run(task=config_device_dry_run, config_dir=Path("custom/configs"))
        ```

    """
    # Use override if provided, otherwise use environment default
    configs_path = config_dir or GENERATED_CONFIGS_FOLDER_PATH
    config_file = Path(configs_path) / f"{task.host.name}.cfg"

    print(f"[DEBUG] - Dry-run: Loading config from {config_file}")

    # Read configuration file
    if not config_file.exists():
        msg = f"Configuration file not found: {config_file}"
        raise FileNotFoundError(msg)

    with config_file.open() as f:
        config = f.read()

    # Load configuration in replace mode
    task.run(
        task=cfg_load_config,
        config=config,
        replace=True,
        privilege_level="privilege_exec",
    )

    # Retrieve the diff
    diff_result = task.run(task=cfg_diff_config)

    # Abort the session (do not commit)
    task.run(task=cfg_abort_config)

    print(f"[DEBUG] - Dry-run complete for {task.host.name}, session aborted")

    # Return the diff as the task result
    return Result(host=task.host, result=diff_result.result)


def config_device_commit(task: Task, config_dir: Path | None = None) -> Result:
    """
    Load configuration, retrieve diff, and commit changes to device.

    This task performs a full configuration operation by loading the
    configuration to a device session, retrieving the diff, and then committing
    the changes to the running configuration.

    Args:
        task: Nornir task object containing host information.
        config_dir: Optional path to directory containing configuration files.
            If not provided, uses GENERATED_CONFIGS_FOLDER_PATH from environment.

    Returns:
        Result object containing the configuration diff as a string.

    Raises:
        FileNotFoundError: If the configuration file for the device is not found.
        Exception: If configuration loading, diff retrieval, or commit fails.

    Example:
        Basic usage with defaults:

        ```python
        result = nr.run(task=config_device_commit)
        for host, multi_result in result.items():
            if not multi_result.failed:
                print(f"Successfully configured {host}")
        ```

        With custom config directory:

        ```python
        result = nr.run(task=config_device_commit, config_dir=Path("custom/configs"))
        ```

    Warning:
        This task commits configuration changes to the device. Always review
        the diff in a dry-run before using this task in production.

    """
    # Use override if provided, otherwise use environment default
    configs_path = config_dir or GENERATED_CONFIGS_FOLDER_PATH
    config_file = Path(configs_path) / f"{task.host.name}.cfg"

    print(f"[DEBUG] - Commit: Loading config from {config_file}")

    # Read configuration file
    if not config_file.exists():
        msg = f"Configuration file not found: {config_file}"
        raise FileNotFoundError(msg)

    with config_file.open() as f:
        config = f.read()

    # Load configuration in replace mode
    task.run(
        task=cfg_load_config,
        config=config,
        replace=True,
        privilege_level="privilege_exec",
    )

    # Retrieve the diff
    diff_result = task.run(task=cfg_diff_config)

    # Display the diff
    if diff_result.result:
        print(f"--- DIFF FOR {task.host.name} ---\n{diff_result.result}")

    # Commit the configuration
    task.run(task=cfg_commit_config, source="running")

    print(f"[DEBUG] - Configuration committed for {task.host.name}")

    # Return the diff as the task result
    return Result(host=task.host, result=diff_result.result)


def config_device_from_file(task: Task) -> None:
    """
    Configure device from a configuration file.

    This is a legacy function maintained for backward compatibility.
    Consider using config_device_dry_run or config_device_commit instead.

    Args:
        task: Nornir task object containing host information.

    """
    config_file = Path(GENERATED_CONFIGS_FOLDER_PATH) / f"{task.host.name}.cfg"
    print(f"[DEBUG] - Configuring device from {config_file}")

    with config_file.open() as f:
        config = f.read()

    # task.run(task=cfg_load_config, config=config)
    # task.run(task=cfg_diff_config)

    # Writing config (Replace)
    # task.run(task=cfg_diff_config)
    # task.run(task=cfg_commit_config)

    task.run(task=cfg_load_config, config=config, replace=True, privilege_level="privilege_exec")

    # Step 2: Retrieve the diff
    # This task returns the 'show session-config diff' output
    diff_result = task.run(task=cfg_diff_config)

    # You can print the diff directly for debugging if needed
    if diff_result.result:
        print(f"--- DIFF FOR {task.host.name} ---\n{diff_result.result}")
        # task.run(task=cfg_abort_config)

    # Committing the config - Closes the connection by default
    task.run(task=cfg_commit_config, source="running")

    # Close the session config


def main():
    nr: Nornir = initialize_nornir()

    # Close all config sessions
    # response = nr.run(task=abort_all_sessions, name="Closing all existing config sessions on the devices")

    # Config the devices
    response: AggregatedResult = nr.run(task=config_device_from_file, name="Task - Applying config to devices")

    print_result(response)


if __name__ == "__main__":
    main()
