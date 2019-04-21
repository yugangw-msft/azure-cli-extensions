# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands.parameters import get_three_state_flag
import azext_aad._help  # pylint: disable=unused-import


class AADCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        aad_custom = CliCommandType(
            operations_tmpl='azext_aad.custom#{}')
        super(AADCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=aad_custom)

    def load_command_table(self, _):
        with self.command_group('ad user') as g:
            g.custom_command('update', 'update_user')
        with self.command_group('ad') as g:
            g.custom_command('list-audit-logs', "list_audit_logs")

        return self.command_table

    def load_arguments(self, _):
        # pylint: disable=line-too-long
        with self.argument_context('ad user update') as c:
            c.argument('display_name', help='the display name of the user')
            c.argument('force_change_password_next_login', arg_type=get_three_state_flag(),
                       help='force change password on next login')
            c.argument('account_enabled', arg_type=get_three_state_flag(),
                       help='enable the user account')
            c.argument('password', help='user password')
            c.argument('upn_or_object_id', help='user principal name or object id')

        with self.argument_context('ad list-audit-logs') as c:
            c.argument('log_type', help='audit log types, e.g. "directoryAudits", "signIns"')


COMMAND_LOADER_CLS = AADCommandsLoader
