# from nornir_utils.plugins.functions import print_result
from nornir.core import Nornir
from nornir.core.filter import F
from nornir.core.task import AggregatedResult, Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_rich.functions import print_result as rprint_result
from nornir_utils.plugins.tasks.files import write_file

from py_netauto.config import GENERATED_CONFIGS_FOLDER_PATH, JINJA_TEMPLATES_FOLDER_PATH
from py_netauto.utils.nornir_helpers import initialize_nornir


def render_configs(task: Task) -> None:
    jinja_templates: dict[str, str] = {
        "leaf": "leaves.j2",
        "spine": "spines.j2",
        "host": "hosts.j2",
        "default": "defaults.j2",
    }
    device_role = task.host.get("role", "default")

    device_template = jinja_templates.get(device_role)

    if not device_template:
        print(f"Skipping Host {task.host.name}: No template mapped for role '{device_role}")
        return

    rendered_config = task.run(
        task=template_file,
        name="Rendering Device config",
        template=device_template,
        path=str(JINJA_TEMPLATES_FOLDER_PATH),
    )

    print(f"[DEBUG] - Writing config at {GENERATED_CONFIGS_FOLDER_PATH}/{task.host.name}.cfg")
    task.run(
        task=write_file,
        filename=f"{GENERATED_CONFIGS_FOLDER_PATH}/{task.host.name}.cfg",
        content=rendered_config[0].result,
    )


def main() -> None:
    nr: Nornir = initialize_nornir()
    print(f"[DEBUG] - Rendering configs using templates at: {JINJA_TEMPLATES_FOLDER_PATH}")
    result: AggregatedResult = nr.run(task=render_configs)

    rprint_result(result)


if __name__ == "__main__":
    main()
