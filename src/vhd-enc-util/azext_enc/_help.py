# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['vm encryption host enable'] = """
    type: command
    short-summary: encrypt VHD using XTS 256-bit cipher model
    examples:
        - name: encrype a VHD and upload to a storage account
          text: |
            az vm encryption vhd enable --vhd-file ~/os_disk.vhd --storage-account myStorageAccount --container vhds --kv /subscriptions/xxxx/resourceGroups/myGroup/providers/Microsoft.KeyVault/vaults/myVault --kek myKey
        - name: encrypt a VHD at local (not uploading to storage)
          text: |
            az vm encryption vhd enable --vhd-file ~/os_disk.vhd --vhd-file-enc ~/os_disk.encrypted.vhd --kv /subscriptions/xxxx/resourceGroups/myGroup/providers/Microsoft.KeyVault/vaults/myVault --kek myKey
"""

helps['vm encryption host rotate-kek'] = """
    type: command
    short-summary: rotate key-vault key encryption key
    examples:
        - name: rotate to a new key encyrption key
          text: |
            az vm encryption host rotate-kek --blob-name os.encrypted.vhd --storage-account myStorageAccount --container vhds --kek hbe-kek2 --kv /subscriptions/xxx/resourceGroups/myGroup/providers/Microsoft.KeyVault/vaults/myVault
"""

helps['vm encryption host show'] = """
    type: command
    short-summary: show encryption status
"""
