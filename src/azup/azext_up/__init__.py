# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType


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


COMMAND_LOADER_CLS = AZUPCommandsLoader
