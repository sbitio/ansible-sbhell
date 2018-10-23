# Based on ansible/plugins/action/shell.py

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash
import os
from tempfile import mkstemp

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        # Shell module is implemented via command
        self._task.action = 'command'
        self._task.args['_uses_shell'] = True

        ### Process sbitio args.

        # free_form feature is restricted to a hardcoded list in parsing/mod_args.py.
        # So we provide the custom 'command' option instead.
        command = self._task.args['command']
        del self._task.args['command']

        # Prepare the command to run.
        log = self._task.args.get('log', dict())
        if log:
          del self._task.args['log']
        if log.get('enabled', True):
            logfile = log.get('logfile', mkstemp())
            # Copy command stdout and stderr to a logfile, while preserving the original file descriptors.
            command = "{ %(command)s 2>&1 1>&3 3>&- | tee -a %(logfile)s; } 3>&1 1>&2 | tee -a %(logfile)s" % {'command': command, 'logfile': logfile[1]}
            display.display("Command output is logged to: " + logfile[1])
        else:
            command = "%(command)s" % {'command': command}

        # This is the internal free form option.
        self._task.args['_raw_params'] = command

        # Ensure the output is registered, if debug logging is enabled.
        if log.get('debug', True) and not self._task.register:
            self._task.register = 'command_result'

        command_action = self._shared_loader_obj.action_loader.get('command',
                                                                   task=self._task,
                                                                   connection=self._connection,
                                                                   play_context=self._play_context,
                                                                   loader=self._loader,
                                                                   templar=self._templar,
                                                                   shared_loader_obj=self._shared_loader_obj)
        result = command_action.run(task_vars=task_vars)

        if log.get('disable', False) and log.get('preserve', True):
            os.unlink(logfile)

        if log.get('debug', True):
            task_vars[self._task.register] = result
            self._task.args = {'var': self._task.register }
            del self._task.register

            debug_action = self._shared_loader_obj.action_loader.get('debug',
                                                                       task=self._task,
                                                                       connection=self._connection,
                                                                       play_context=self._play_context,
                                                                       loader=self._loader,
                                                                       templar=self._templar,
                                                                       shared_loader_obj=self._shared_loader_obj)
            debug_result = debug_action.run(task_vars=task_vars)
            result = debug_result

        return result
