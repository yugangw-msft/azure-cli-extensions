# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import os.path
import json
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.commands.client_factory import get_mgmt_service_client

logger = get_logger(__name__)


def _get_infra_names():
    from azure.cli.core._profile import Profile  # todo perf
    user = Profile().get_current_account_user()
    user = user.split('@', 1)[0]
    # logger.warning('looking for .csproj')
    cwd = os.environ.get('NOW_TEST_DIR') or os.getcwd()
    from os.path import basename
    prj = basename(cwd)
    base_name = user + '-' + prj.rsplit('.', 1)[0]
    return cwd, base_name, base_name, 'eastus2'


def down(cmd):
    from msrestazure.azure_exceptions import CloudError
    _, base_name, resource_group_name, _ = _get_infra_names()
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    container_client = get_mgmt_service_client(cmd.cli_ctx, ContainerInstanceManagementClient)
    container_name = (base_name + '-container').lower()[:63]
    try:
        container_client.container_groups.get(resource_group_name, container_name)
    except CloudError:
        logger.warning('Nothing to clean up')
        return
    logger.warning('Deleting %s', container_name)
    container_client.container_groups.delete(resource_group_name, container_name)


def up(cmd, launch_browser=None, attach=None, ports=None, databases=None, start_up_cmd=None):
    import time
    from msrestazure.azure_exceptions import CloudError

    cwd, base_name, resource_group_name, location = _get_infra_names()
    ports = ports or [80]
    ports.append(50051)
    items = os.listdir(cwd)
    aznow_json = os.path.join(cwd, 'aznow.json')
    aznow_json_exists = os.path.exists(aznow_json)
    if next((f for f in items if f.endswith('.csproj') or f.endswith('.vbproj')), None):
        image = 'neverland123/agent:dotnet-slim.2.2.104'
        if not aznow_json_exists:
            with open(aznow_json, 'w') as file_handler:
                file_handler.write(json.dumps({
                    "sourceDirectory": "",
                    "commandTriggerDirectory": "bin",
                    "targetDirectory": "/az-app",
                    "runCommands": [
                        {"command": ["dotnet", "restore"]},
                        {"command": start_up_cmd.split() if start_up_cmd else ["dotnet", "run", "--no-launch-profile"]}
                    ],
                    "cleanupProcesses": ["dotnet"],
                    "useIgnoreRules": ["docker"]
                }))
    elif next((f for f in items if f.endswith('package.json') or f.endswith('node_modules'))):
        image = 'neverland123/agent:node-slim'
        if not aznow_json_exists:
            with open(aznow_json, 'w') as file_handler:
                file_handler.write(json.dumps({
                    "targetDirectory": "/az-app",
                    "runCommands": [
                        {
                            "glob": "package.json",
                            "command": ["npm", "update"]
                        },
                        {
                            "command": start_up_cmd.split() if start_up_cmd else ["npm", "start"]
                        }
                    ],
                    "cleanupProcesses": ["node"],
                    "useIgnoreRules": ["docker", "nodejs"]
                }))
    else:
        raise CLIError("Can't find right code projects for .NET or NodeJS")
    os.chdir(cwd)

    # get project file under folder
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    container_client = get_mgmt_service_client(cmd.cli_ctx, ContainerInstanceManagementClient)
    container_name = (base_name + '-container').lower()[:63]
    try:
        container_group = container_client.container_groups.get(resource_group_name, container_name)
    except CloudError:
        container_group = None

    environment_variables = None
    if databases:
        databases = [d.lower() for d in databases]
        az_up_env_vars = [(k[k.lower().index('az_up_') + len('az_up_'):], k)
                          for k in os.environ if k.lower().startswith('az_up_')]
        env_vars_to_copy = [env_var for suffix, env_var in az_up_env_vars
                            if suffix.lower() in databases or env_var.lower() in databases]
        environment_variables = [{'name': k, 'secure_value': os.environ[k]} for k in env_vars_to_copy]

    to_create_container = not container_group
    if container_group and environment_variables:
        provisioned_env_vars = [x.name for x in container_group.containers[0].environment_variables]
        if provisioned_env_vars != env_vars_to_copy:
            to_create_container = True
        else:
            logger.warning('Same data connections are already set, skipping')

    if to_create_container:
        # create RG
        logger.warning('One time configuration...')
        logger.warning('    Creating a resource group "%s"', resource_group_name)

        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        t_resource_group = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   'models#ResourceGroup')
        resource_client.resource_groups.create_or_update(resource_group_name,
                                                         t_resource_group(location=location))
        # create a container instance
        t = time.time()
        logger.warning('    Creating needed infrastructure to run you code')
        logger.info('    Provisioned a container instance "%s" with image of "%s"', container_name, image)
        container_group = create_container_instance(cmd, container_client, location, resource_group_name,
                                                    container_name, image, base_name, ports, environment_variables)
        logger.warning('Done (%s sec)', int(time.time() - t))
        container = container_group.containers[0]
        if container.instance_view.current_state.state == 'Error':
            log = container_client.container.list_logs(resource_group_name, container_name, container_name)
            raise CLIError(log.content)

    fqdn = container_group.ip_address.fqdn
    site_url = 'http://{}:{}'.format(fqdn, ports[0])  # Get port?

    result = sync_code(cwd, container_group.ip_address.ip,
                       site_url, attach=attach, launch_browser=launch_browser)
    if not result:
        logger.warning('connection error occurred, retry one more time')
        time.sleep(3)
        result = sync_code(cwd, container_group.ip_address.ip,
                           site_url, attach=attach, launch_browser=launch_browser)
    if not result:
        raise CLIError('Failed to provision the code in cloud. Please refer to command output for details ')


def sync_code(cwd, public_ip, launch_url, attach, launch_browser):
    import platform
    from subprocess import Popen, PIPE
    import shlex
    import tempfile

    ext_folder = os.path.dirname(os.path.realpath(__file__))
    sync_tool_folder = os.path.join(ext_folder, 'sync_tool')
    sync_tool_exe = os.path.join(sync_tool_folder, 'aznow')

    system = platform.system()
    if system == 'Windows':
        sync_tool_exe += '.exe'

    if not os.path.isfile(sync_tool_exe):
        if system == 'Windows':
            zip_file = 'win-x64.zip'
        elif system == 'Linux':
            zip_file = 'linux-x64.zip'
        elif system == 'Darwin':
            zip_file = 'osx-x64.zip'
        else:
            raise CLIError('No sync tool available to publish your code')

        import stat
        import zipfile
        from six.moves.urllib.request import urlretrieve
        zip_file_uri = 'https://azureclitemp.blob.core.windows.net/azup/' + zip_file
        setup_file = os.path.join(tempfile.mkdtemp(), zip_file)
        logger.info('Downloading sync tool from %s', zip_file_uri)
        urlretrieve(zip_file_uri, setup_file)
        zip_ref = zipfile.ZipFile(setup_file, 'r')
        zip_ref.extractall(sync_tool_folder)
        zip_ref.close()
        if system in ['Linux', 'Darwin']:
            st = os.stat(sync_tool_exe)
            os.chmod(sync_tool_exe, st.st_mode | stat.S_IEXEC)

    cmd = '"{}" deploy --host {} --port 50051'.format(sync_tool_exe, public_ip)

    process = Popen(shlex.split(cmd), stdout=PIPE)
    result = True
    while True:
        output = process.stdout.readline().decode()
        if output:
            output = output.strip()
            if 'System.Net.Http.HttpRequestException' in output:
                process.kill()
                result = False
                break
            print(output)
            if 'listening on' in output or 'start /az-app' in output:  # netcore or nodejs
                if launch_browser:
                    from azure.cli.core.util import open_page_in_browser
                    logger.warning('Site uri: %s. Let us Launch it in browser...', launch_url)
                    open_page_in_browser(launch_url)
                else:
                    logger.warning('Site uri: %s.', launch_url)
                if not attach:
                    process.kill()
                    break

    return result

    # (out, err) = process.communicate()
    #   TODO: 1. exit code from the npm or dotnet and verify we capture all provision errors
    #         2. output the npm/dotnet logs
    #         3. Corss check skip the right files
    #         4. Port


def create_container_instance(cmd, client, location, resource_group_name, name, image, dns_name_label, ports,
                              environment_variables):
    from azure.mgmt.containerinstance.models import (Container, ContainerGroup, ContainerGroupNetworkProtocol,
                                                     ContainerPort, IpAddress, Port, ResourceRequests,
                                                     ResourceRequirements, ContainerGroupIpAddressType)

    protocol = ContainerGroupNetworkProtocol.tcp

    container_resource_requests = ResourceRequests(memory_in_gb=1.5, cpu=1)
    container_resource_requirements = ResourceRequirements(requests=container_resource_requests)

    cgroup_ip_address = IpAddress(ports=[Port(protocol=protocol, port=p) for p in ports],
                                  dns_name_label=dns_name_label, type=ContainerGroupIpAddressType.public)

    container = Container(name=name,
                          image=image,
                          resources=container_resource_requirements,
                          ports=[ContainerPort(
                              port=p, protocol=protocol) for p in ports] if cgroup_ip_address else None,
                          environment_variables=environment_variables)

    cgroup = ContainerGroup(location=location,
                            containers=[container],
                            os_type='Linux',
                            ip_address=cgroup_ip_address,
                            restart_policy='Always')
    client.config.long_running_operation_timeout = 10
    poller = client.container_groups.create_or_update(resource_group_name, name, cgroup)
    return LongRunningOperation(cmd.cli_ctx)(poller)
