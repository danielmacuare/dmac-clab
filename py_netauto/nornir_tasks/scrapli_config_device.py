from nornir.core import Nornir
from nornir.core.task import AggregatedResult, Task
from nornir_rich.functions import print_result
from nornir_scrapli.tasks import cfg_abort_config, cfg_commit_config, cfg_diff_config, cfg_load_config, send_command

from py_netauto.utils.nornir_helpers import GENERATED_CONFIGS_FOLDER_PATH, initialize_nornir


def abort_all_sessions(task):
    # 1. Get the list of sessions
    # Arista output for 'show configuration sessions' includes names of pending sessions.
    output = task.run(task=send_command, command="show configuration sessions").result
    print(f"Output: {output}")

    # 2. Parse the output for session names (simple check for pending sessions)
    for line in output.splitlines():
        # Scrapli sessions usually look like 'scrapli_cfg_...'
        if "pending" in line.lower() or "scrapli_cfg" in line:
            # Extract the session name (usually the first word in the line)
            session_name = line.split()[0]  # If starts with scrapli_cfg
            # session_name = line.split()[1]  # If statrts with *

            # 3. Enter the session and abort it
            task.run(task=send_command, command=f"configure session {session_name}")
            task.run(task=send_command, command="abort")
            print(f"Aborted session: {session_name} on {task.host.name}")


def config_device_from_file(task: Task) -> None:
    config_file = f"{GENERATED_CONFIGS_FOLDER_PATH}/{task.host.name}.cfg"
    print(f"[DEBUG] - Configuring device from {config_file}")

    with open(config_file) as f:
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
