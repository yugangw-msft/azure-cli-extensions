# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError
from knack.log import get_logger

from azure.graphrbac.models import UserUpdateParameters, PasswordProfile
logger = get_logger(__name__)


def update_user(cmd, upn_or_object_id, display_name=None, force_change_password_next_login=None, password=None,
                account_enabled=None, mail_nickname=None):
    password_profile = None
    if force_change_password_next_login is not None or password is not None:
        password_profile = PasswordProfile(password=password,
                                           force_change_password_next_login=force_change_password_next_login)

    update_parameters = UserUpdateParameters(display_name=display_name, password_profile=password_profile,
                                             account_enabled=account_enabled, mail_nickname=mail_nickname)
    graph_client = _graph_client_factory(cmd.cli_ctx)
    return graph_client.users.update(upn_or_object_id=upn_or_object_id, parameters=update_parameters)


def list_audit_logs(cmd, log_type):
    import json
    import uuid
    import requests
    from azure.cli.core._profile import Profile
    from azure.cli.core.util import should_disable_connection_verify
    from azure.cli.core.commands.client_factory import UA_AGENT

    profile = Profile(cli_ctx=cmd.cli_ctx)
    ms_graph_resource = 'https://graph.microsoft.com/'
    if cmd.cli_ctx.cloud.name == 'AzureUSGovernment':
        ms_graph_resource = 'https://graph.microsoft.us/'
    elif cmd.cli_ctx.cloud.name == 'AzureChinaCloud':
        ms_graph_resource = 'https://microsoftgraph.chinacloudapi.cn'
    audit_logs_url = ms_graph_resource + 'beta/auditLogs/' + log_type

    access_token = profile.get_raw_token(ms_graph_resource)
    headers = {
        'Authorization': "Bearer " + access_token[0][1],
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'x-ms-client-request-id': str(uuid.uuid4()),
        'User-Agent': UA_AGENT
    }
    response = requests.get(audit_logs_url, headers=headers, verify=not should_disable_connection_verify())
    if not response.ok:
        raise CLIError(response.reason)
    return json.loads(response.content.decode())


def _graph_client_factory(cli_ctx, **_):
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import configure_common_settings
    from azure.graphrbac import GraphRbacManagementClient
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    client = GraphRbacManagementClient(cred, tenant_id,
                                       base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    configure_common_settings(cli_ctx, client)
    return client
