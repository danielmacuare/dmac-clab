# from nornir_utils.plugins.functions import print_result
from pathlib import Path

from nornir.core import Nornir
from nornir.core.task import AggregatedResult, MultiResult, Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_rich.functions import print_result as rprint_result
from nornir_utils.plugins.tasks.files import write_file

from py_netauto.config import GENERATED_CONFIGS_FOLDER_PATH, JINJA_TEMPLATES_FOLDER_PATH
from py_netauto.utils.nornir_helpers import initialize_nornir


def render_configs(
    task: Task,
    templates_path: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """
    Render device configuration from Jinja2 template.

    This task renders a device configuration using a Jinja2 template based on the
    device's role. The rendered configuration is written to a file in the output
    directory.

    Args:
        task: Nornir task object containing host information.
        templates_path: Optional path to Jinja2 templates directory. If not provided,
            uses JINJA_TEMPLATES_FOLDER_PATH from environment configuration.
        output_path: Optional path to output directory for generated configs. If not
            provided, uses GENERATED_CONFIGS_FOLDER_PATH from environment configuration.

    Returns:
        None. The task writes the rendered configuration to a file.

    Raises:
        FileNotFoundError: If the template file is not found.
        PermissionError: If the output directory is not writable.

    Example:
        Basic usage with defaults:

        ```python
        nr.run(task=render_configs)
        ```

        With path overrides:

        ```python
        nr.run(task=render_configs, templates_path=Path("custom/templates"), output_path=Path("custom/output"))
        ```

    """
    # Use overrides if provided, otherwise use environment defaults
    templates_dir = templates_path or JINJA_TEMPLATES_FOLDER_PATH
    output_dir = output_path or GENERATED_CONFIGS_FOLDER_PATH

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

    rendered_config: MultiResult = task.run(
        task=template_file,
        name="Rendering Device config",
        template=device_template,
        path=str(templates_dir),
    )

    output_file = f"{output_dir}/{task.host.name}.cfg"
    print(f"[DEBUG] - Writing config at {output_file}")
    task.run(
        task=write_file,
        name="Writing configs to disk",
        filename=output_file,
        content=rendered_config[0].result,
    )


def main() -> None:
    nr: Nornir = initialize_nornir()
    print(f"[DEBUG] - Rendering configs using templates at: {JINJA_TEMPLATES_FOLDER_PATH}")
    result: AggregatedResult = nr.run(task=render_configs)

    rprint_result(result)


if __name__ == "__main__":
    main()
