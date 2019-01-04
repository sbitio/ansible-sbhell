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

    def getParam(self, param, default = None):
        """
        Obtains the value for a parameter from task arguments,
        a variable or the provided default.

        The parameter name matches `param`. In the case of variables
        'drush_' prefix is added.
        """
        value = self.task_vars.get('drush_' + param, default)
        if self._task.args.has_key(param):
            value = self._task.args[param]
            del self._task.args[param]

        return self._templar.template(value)


    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        # Shell module is implemented via command
        self._task.action = 'sbhell'

        self.task_vars = task_vars

        # Pick settings from vars or fallback to defaults.
        _drush   = self.getParam('executable', 'drush')
        _args    = self.getParam('args', '-y --nocolor')
        _alias   = self.getParam('alias', '@none')
        _command = self.getParam('command', 'status')
        _memory  = self.getParam('memory_limit')

        env = {}
        env['CACHE_PREFIX'] = '/tmp/drush-cache/%s' % _alias,
        if _memory:
          env['PHP_OPTIONS'] = '-d memory_limit="%s"' % _memory

        self._task.args['command'] = "%s %s %s %s" % (_drush, _alias, _args, _command)
        self._task.environment = env

        command_action = self._shared_loader_obj.action_loader.get(self._task.action,
                                                                   task=self._task,
                                                                   connection=self._connection,
                                                                   play_context=self._play_context,
                                                                   loader=self._loader,
                                                                   templar=self._templar,
                                                                   shared_loader_obj=self._shared_loader_obj)
        result = command_action.run(task_vars=task_vars)

        return result
