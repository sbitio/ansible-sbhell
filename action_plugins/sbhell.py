# Based on ansible/plugins/action/shell.py

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash
import os
import re
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
        log = self._task.args.get('log', dict())
        if log is False:
            log = {
                'enabled': False,
                'debug': False,
            }

        # '_raw_params' is the free_form feature. It is is restricted to
        # a hardcoded list in parsing/mod_args.py.
        # So we accept the command to run in the 'command' option instead.
        # The provided command is enriched with our execution options
        # (pipefail, logging,..) and assigned to the free_form option.

        # Additionally, ensure we do this only once because the args
        # are preserved across iterations in retrying tasks ('until: ...').
        initialized = self._task.args.has_key('_raw_params')

        if not initialized:
            command = self._task.args.get('command')
            del self._task.args['command']

            # Set /bin/bash to support set -o pipefail.
            if not self._task.args.has_key('executable'):
                self._task.args['executable'] = '/bin/bash'

            # Prepare the command to run.
            if log:
              del self._task.args['log']
            if log.get('enabled', True):
                logfile_default = '-'.join([
                    '/tmp/ansible-sbhell',
                    re.sub('\W+','_', self._task.name.lower()[:80]),
                    str(uuid.uuid4())
                ])
                logfile = log.get('logfile', logfile_default)
                # Copy command stdout and stderr to a logfile, while preserving the original file descriptors.
                command = "set -o pipefail; { %(command)s 2>&1 1>&3 3>&- | tee -a %(logfile)s; } 3>&1 1>&2 | tee -a %(logfile)s" % {'command': command, 'logfile': logfile}

                # Inform the user of the logfile.
                if task_vars.has_key('item'):
                    prefix = "[%s] => (item=%s)" % (task_vars['inventory_hostname'], task_vars['item'])
                else:
                    prefix = "[%s]" % task_vars['inventory_hostname']
                display.display("%s Command output is logged to: %s" % (prefix, logfile))
                if not log.get('preserve', True):
                    command += '; rm %s' % logfile

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
            debug = self._templar.template(result, convert_bare=True, fail_on_undefined=True)
            result['_ansible_verbose_always'] = True
            result[self._task.register] = debug

            # Green message is nice.
            result['changed'] = False

        return result
