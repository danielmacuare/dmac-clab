# from nornir_utils.plugins.functions import print_result
from nornir.core import Nornir
from nornir.core.filter import F
from nornir.core.task import AggregatedResult, Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_rich.functions import print_result as rprint_result

from py_netauto.utils.nornir_helpers import initialize_nornir


def render_configs(task: Task):
    _ = task.run(
        task=template_file,
        name="Basec config",
        template="l1.j2",
        path="/home/dmac/repos/dmac-clab/arista/dmac/evpn-vxlan-l3gw/nornir/templates",
    )


def main():
    nr: Nornir = initialize_nornir()
    result: AggregatedResult = nr.run(task=render_configs)

    rprint_result(result)


if __name__ == "__main__":
    main()
