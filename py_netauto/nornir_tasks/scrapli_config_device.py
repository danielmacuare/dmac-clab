from nornir.core import Nornir
from nornir.core.task import AggregatedResult, Task
from nornir_rich.functions import print_result
from nornir_scrapli.tasks import send_configs_from_file

from py_netauto.utils.nornir_helpers import GENERATED_CONFIGS_FOLDER_PATH, initialize_nornir


def config_device_from_file(task: Task) -> None:
    print(f"[DEBUG] - Configuring device from {GENERATED_CONFIGS_FOLDER_PATH}/{task.host.name}.cfg")
    task.run(
        task=send_configs_from_file,
        file=f"{GENERATED_CONFIGS_FOLDER_PATH}/{task.host.name}.cfg",
        stop_on_failed=True,
    )


def main():
    nr: Nornir = initialize_nornir()
    response: AggregatedResult = nr.run(task=config_device_from_file, name="Task - Applying config to devices")
    # If you want to get a print_result:
    print_result(response)


if __name__ == "__main__":
    main()
