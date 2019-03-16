# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType


def _secure_environment_variables_type(value):
    """Space-separated values in 'key=value' format."""
    try:
        env_name, env_secure_value = value.split('=', 1)
        return {'name': env_name, 'secureValue': env_secure_value}
    except ValueError:
        message = ("Incorrectly formatted secure environment settings. "
                   "Argument values should be in the format a=b c=d")
        raise CLIError(message)


class AZUPCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        azup_custom = CliCommandType(
            operations_tmpl='azext_up.custom#{}')
        super(AZUPCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                 custom_command_type=azup_custom)

    def load_command_table(self, _):
        with self.command_group('') as g:
            g.custom_command('up', 'up')
            g.custom_command('down', 'down')

        return self.command_table

    def load_arguments(self, _):
        # pylint: disable=line-too-long
        from knack.arguments import CLIArgumentType
        with self.argument_context('up') as c:
            c.argument('launch_browser', options_list=['--launch-browser', '-l'], action='store_true', help='launch browser after deployment')
            c.argument('attach', options_list=['--attach', '-a'], action='store_true', help='attach standard output and error streams. Ctrl+C to stop')
            c.argument('ports', type=int, nargs='*', options_list=['--ports', '-p'], help='space separated web site ports. Default to 80')
            c.argument('databases', nargs='*',
                       help='Space separated azure database server name. "az up" securely deploys connection strings set through env variables named as "AZ_UP_<SERVERNAME>..."')
            c.argument('start_up_cmd', help='if specified, az up will use it to start the web after code is deployed')


COMMAND_LOADER_CLS = AZUPCommandsLoader
