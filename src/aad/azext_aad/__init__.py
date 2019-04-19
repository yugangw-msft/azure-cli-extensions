# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType

import azext_aad._help  # pylint: disable=unused-import


class AADCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        aad_custom = CliCommandType(
            operations_tmpl='azext_add.custom#{}')
        super(AADCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=aad_custom)

    def load_command_table(self, _):
        with self.command_group('ad user') as g:
            g.custom_command('update', 'update_user')

        return self.command_table

    def load_arguments(self, _):
        # pylint: disable=line-too-long
        from knack.arguments import CLIArgumentType

        with self.argument_context('ad user') as c:
            c.argument('display_name, help='the display name of the user')


COMMAND_LOADER_CLS = AADCommandsLoader
