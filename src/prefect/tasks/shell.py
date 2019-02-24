import os
import subprocess
from typing import Any

import prefect
from prefect.utilities.tasks import defaults_from_attrs


class ShellTask(prefect.Task):
    """
    Task for running arbitrary shell commands.

    Args:
        - command (string, optional): shell command to be executed; can also be
            provided post-initialization by calling this task instance
        - cd (string, optional): string specifying the absolute path to a
            directory to run the `command` from
        - env (dict, optional): dictionary of environment variables to use for
            the subprocess; can also be provided at runtime
        - shell (string, optional): shell to run the command with; defaults to "bash"
        - **kwargs: additional keyword arguments to pass to the Task constructor

    Example:
        ```python
        from prefect import Flow
        from prefect.tasks.shell import ShellTask

        task = ShellTask(cd='/usr/bin')
        with Flow() as f:
            res = task(command='ls')

        out = f.run(return_tasks=[res])
        ```
    """

    def __init__(
        self,
        command: str = None,
        cd: str = None,
        env: dict = None,
        shell: str = "bash",
        **kwargs: Any
    ):
        self.command = command
        self.cd = cd
        self.env = env
        self.shell = shell
        super().__init__(**kwargs)

    @defaults_from_attrs("command", "env")
    def run(self, command: str = None, env: dict = None) -> bytes:  # type: ignore
        """
        Run the shell command.

        Args:
            - command (string): shell command to be executed; can also be
                provided at task initialization
            - env (dict, optional): dictionary of environment variables to use for
                the subprocess

        Returns:
            - stdout + stderr (bytes): anything printed to standard out /
                standard error during command execution

        Raises:
            - prefect.engine.signals.FAIL: if command has an exit code other
                than 0
        """
        if command is None:
            raise TypeError("run() missing required argument: 'command'")

        if self.cd is not None:
            command = "cd {} && ".format(self.cd) + command

        current_env = os.environ.copy()
        current_env.update(env or {})
        try:
            out = subprocess.check_output(
                [self.shell, "-c", command], stderr=subprocess.STDOUT, env=current_env
            )
        except subprocess.CalledProcessError as exc:
            msg = "Command failed with exit code {0}: {1}".format(
                exc.returncode, exc.output
            )
            raise prefect.engine.signals.FAIL(msg) from None
        return out
