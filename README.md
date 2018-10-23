Ansible s(b)hell
================

Ansible role providing modules (action plugins) to ease shell invocations.

At present it provides two modules:

 * `sbhell`: shell invocations with extra logging capabilities.
 * `drush`: Drush invocations via sbhell.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

```yaml
    - hosts: localhost
      vars:
        drush_executable   : '/opt/drush/9/drush'
        drush_memory_limit : '3072M'

      roles:
         - { role: ansible-sbhell, drush_args: '-y --no-ansi' }
      post_tasks:
				- name: test shell
					sbhell:
					args:
						command: 'ls /'
						log:
							enabled: true
							debug: true
							preserve: false

				- name: test drush
					drush:
					args:
						alias: '@d7'
						command: php-eval "return ini_get(\"memory_limit\")"
```


License
-------

MIT

Author Information
------------------

SB IT Media, S.L.
