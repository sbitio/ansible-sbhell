# Based on ansible/plugins/action/shell.py

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash
import os
import uuid

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
            logfile = log.get('logfile', '/tmp/ansible-sbhell-' + str(uuid.uuid4()))
            # Copy command stdout and stderr to a logfile, while preserving the original file descriptors.
            command = "{ %(command)s 2>&1 1>&3 3>&- | tee -a %(logfile)s; } 3>&1 1>&2 | tee -a %(logfile)s" % {'command': command, 'logfile': logfile}
            display.display("Command output is logged to: " + logfile)
            if not log.get('preserve', True):
                command += '; rm %s' % logfile
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


        if log.get('debug', True):
            # Format the result as the debug module does.
            debug = self._templar.template(result, convert_bare=True, fail_on_undefined=True, bare_deprecated=False)
            result['_ansible_verbose_always'] = True
            result[self._task.register] = debug

            # Green message is nice.
            result['changed'] = False
            # Drop unneccesary output.
            del result['stdout']

        return result
