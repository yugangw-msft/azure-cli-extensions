# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azext_enc._help  # pylint: disable=unused-import


class ENCCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        enc_custom = CliCommandType(
            operations_tmpl='azext_enc.custom#{}')
        super(ENCCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=enc_custom)

    def load_command_table(self, _):
        with self.command_group('vm encryption') as g:
            g.custom_command('host enable', 'client_side_encrypt')
            g.custom_command('host rotate-kek', 'rotate_kek')
            g.custom_command('host show', 'show_encryption_status')
        return self.command_table

    def load_arguments(self, _):
        # pylint: disable=line-too-long
        with self.argument_context('vm encryption host enable') as c:
            c.argument('key_encryption_keyvault', options_list=['--key-encryption-keyvault', '--kv'], help='key vault resource id')
            c.argument('key_encryption_key', options_list=['--key-encryption-key', '--kek'], help='key vault key name or id')
            c.argument('vhd_file', options_list=['--vhd-file', '-f'], help='VHD file to encrypt')
            c.argument('blob_name', options_list=['--blob-name', '-b'], help='the name of the storage blob which the encrypted VHD get uploaded to. Default to the VHD file name')
            c.argument('container', options_list=['--container', '-c'], help='the storage container of the VHD blob')
            c.argument('storage_account', help='the storage account of the VHD blob')
            c.argument('vhd_file_enc', help="File name of encrypted VHD. This is required if you don't want to upload to storage")
            c.argument('no_progress', action='store_true', help="disable progress reporting")
            c.argument('max_connections', help="Maximum number of parallel connections to use to upload encrypted VHD")
            c.argument('staging_dir', help="staging folder to contain the temporary encrypted VHD before upload to the storage account. Default to the temp folder")

        with self.argument_context('vm encryption host rotate-kek') as c:
            c.argument('key_encryption_keyvault', options_list=['--key-encryption-keyvault', '--kv'], help='key vault resource id')
            c.argument('key_encryption_key', options_list=['--key-encryption-key', '--kek'], help='key vault key name or id')
            c.argument('blob_name', options_list=['--blob-name', '-b'], help='the name of the VHD blob')
            c.argument('container', options_list=['--container', '-c'], help='the storage container of the VHD blob')
            c.argument('storage_account', help='the storage account of the VHD blob')

        with self.argument_context('vm encryption host show') as c:
            c.argument('vm_name', options_list=['-n', '--name'], help='The name of the Virtual Machine', id_part='name')


COMMAND_LOADER_CLS = ENCCommandsLoader
