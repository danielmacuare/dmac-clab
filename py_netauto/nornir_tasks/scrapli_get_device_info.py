from nornir.core import Nornir
from nornir.core.task import AggregatedResult, Task
from nornir_rich.functions import print_result
from nornir_scrapli.functions import print_structured_result
from nornir_scrapli.tasks import send_command

from py_netauto.utils.nornir_helpers import initialize_nornir


def get_devices_info(task: Task) -> None:
    task.run(
        task=send_command,
        command="show lldp neighbors",
    )


def main():
    nr: Nornir = initialize_nornir()
    response: AggregatedResult = nr.run(task=get_devices_info, name="Task - Getting info from network devices")
    # If you want to get a print_result:
    print_result(response)
    # If you want to get strucutred data back use the following:
    # print_structured_result(response)


if __name__ == "__main__":
    main()
