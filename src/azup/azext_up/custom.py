# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import os.path
import json
import re
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


def up(cmd, launch_browser=None, attach=None, ports=None, start_up_cmd=None):
    import time
    from msrestazure.azure_exceptions import CloudError

    cwd, base_name, resource_group_name, location = _get_infra_names()
    ports_to_open = [50051] + (ports or [80])

    items = os.listdir(cwd)
    aznow_json = os.path.join(cwd, 'aznow.json')
    is_python_django = False
    if next((f for f in items if f.endswith('.csproj') or f.endswith('.vbproj')), None):
        image = 'neverland123/agent:dotnet-slim.2.2.104'
        az_now_json = {
            "sourceDirectory": "",
            "commandTriggerDirectory": "bin",
            "targetDirectory": "/az-app",
            "runCommands": [
                {"command": ["dotnet", "restore"]},
                {"command": start_up_cmd.split() if start_up_cmd else ["dotnet", "run", "--no-launch-profile"]}
            ],
            "cleanupProcesses": ["dotnet"],
            "useIgnoreRules": ["docker"]
        }
    elif next((f for f in items if f.endswith('package.json') or f.endswith('node_modules')), None):
        if not ports:
            ports_to_open.append(3000)
        image = 'neverland123/agent:node-slim'
        az_now_json = {
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
        }
    elif next((f for f in items if f.endswith('manage.py')), None):  # TODO, finalize the detecting logics
        is_python_django = True
        image = 'neverland123/agent:python'
        az_now_json = {
            "targetDirectory": "/az-app",
            "runCommands": [
                {
                    "glob": "requirements.txt",
                    "command": ["pip", "install", "-r", "requirements.txt"]
                },
                {
                    "command": start_up_cmd.split() if start_up_cmd else ("python manage.py runserver 0.0.0.0:{}".format(ports_to_open[-1])).split()
                }
            ],
            "cleanupProcesses": ["python"],
            "useIgnoreRules": ["docker", "python"]
        }
    else:
        raise CLIError('Could not find suitable project to deploy. "az up" works with .Net Core 2.x, Node Express and Python Django')

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
    db_conn_mark = 'AZ_UP_'
    az_up_env_vars = [k for k in os.environ if k.startswith(db_conn_mark)]
    # TODO: warn that we found and will only process one connection
    if len(az_up_env_vars) > 1:
        logger.warning('We found a few database connections "{}", only "{}" will be handled'.format(
            ','.join(az_up_env_vars), az_up_env_vars[0]))
    if az_up_env_vars:
        conn_name, conn = az_up_env_vars[0], os.environ[az_up_env_vars[0]]
        if is_python_django:
            key_values = {k: None for k in ['user', 'password', 'host', 'port', 'database']}
            for k in key_values.keys():
                exp = k + '=[\'"](.+?)[\'"]'
                r = re.search(exp, conn)
                if not r:
                    raise CLIError('Could not find the "{}" field in the connection string'.format(k))
                key_values[k] = r.group(1)
            # we leverage django-heroku which uses DATABASE_URL
            environment_variables = [{'name': 'DATABASE_URL', 'secure_value': 'postgres://{user}:{password}@{host}:{port}/{database}'.format(**key_values)}]
            runCommands = az_now_json['runCommands']
            runCommands.insert(len(runCommands) - 1, {"command": ["python", "manage.py", "migrate"]})
            runCommands.insert(len(runCommands) - 1, {"command": ["python", "manage.py", "loaddata", "initial_data"]})
        else:
            environment_variables = [{'name': conn_name, 'secure_value': conn}]

    to_create_container = not container_group
    if container_group and environment_variables:
        to_create_container = True
        provisioned_env_vars = [x.name for x in container_group.containers[0].environment_variables]
        if not set(az_up_env_vars).issubset(set(provisioned_env_vars)):
            to_create_container = True
        else:
            logger.warning('Same data connections are already set, skipping')

    with open(aznow_json, 'w') as file_handler:
        file_handler.write(json.dumps(az_now_json))

    if is_python_django:
        patch_django_for_azure(cwd)

    if to_create_container:
        # create RG
        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        t_resource_group = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   'models#ResourceGroup')
        if not resource_client.resource_groups.check_existence(resource_group_name):
            logger.warning('Creating a resource group "%s"', resource_group_name)
            resource_client.resource_groups.create_or_update(resource_group_name,
                                                             t_resource_group(location=location))
        # create a container instance
        t = time.time()
        logger.warning('Creating infrastructure needed to run your code')
        logger.info('Provisioned a container instance "%s" with image of "%s"', container_name, image)
        container_group = create_container_instance(cmd, container_client, location, resource_group_name,
                                                    container_name, image, base_name,
                                                    ports_to_open, environment_variables)
        logger.warning('Done (%s sec)', int(time.time() - t))
        container = container_group.containers[0]
        if container.instance_view.current_state.state == 'Error':
            log = container_client.container.list_logs(resource_group_name, container_name, container_name)
            raise CLIError(log.content)

    fqdn = container_group.ip_address.fqdn
    site_url = 'http://{}:{}'.format(fqdn, ports_to_open[-1])

    result = sync_code(cwd, container_group.ip_address.ip,
                       site_url, attach=attach, launch_browser=launch_browser,
                       sentinel_text='Operations to perform:' if is_python_django else None)
    if not result:
        logger.warning('connection error occurred, retry one more time')
        time.sleep(3)
        result = sync_code(cwd, container_group.ip_address.ip, site_url, attach=attach, launch_browser=launch_browser,
                           sentinel_text='Operations to perform:' if is_python_django else None)
    if not result:
        raise CLIError('Failed to provision the code in cloud. Please refer to command output for details')


def download_sync_tool(system, sync_tool_folder, sync_tool_exe):
    import tempfile
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


def sync_code(cwd, public_ip, launch_url, attach, launch_browser, sentinel_text=None):
    import datetime
    import platform
    from subprocess import Popen, PIPE
    import shlex
    import sys
    from threading import Thread
    from azure.cli.core.util import open_page_in_browser

    try:
        from queue import Queue, Empty
    except ImportError:
        from Queue import Queue, Empty  # python 2.x

    ON_POSIX = 'posix' in sys.builtin_module_names

    def enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    ext_folder = os.path.dirname(os.path.realpath(__file__))
    sync_tool_folder = os.path.join(ext_folder, 'sync_tool')
    sync_tool_exe = os.path.join(sync_tool_folder, 'aznow')

    system = platform.system()
    if system == 'Windows':
        sync_tool_exe += '.exe'

    if not os.path.isfile(sync_tool_exe):
        download_sync_tool(system, sync_tool_folder, sync_tool_exe)

    cmd = '"{}" deploy --host {} --port 50051'.format(sync_tool_exe, public_ip)

    process = Popen(shlex.split(cmd), stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
    q = Queue()
    t = Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True
    t.start()

    result = True
    output, empty_time, idle_time_limit_in_sec = None, None, 60
    while True:
        try:
            output = q.get_nowait()
        except Empty:
            output = b''
        output = output.decode()
        output = output.strip() if output else ''
        if output:
            empty_time = None
            output = output.strip()
            if 'System.Net.Http.HttpRequestException' in output:
                process.kill()
                result = False
                break
            print(output)
            if ('listening on' in output or 'start /az-app' in output):
                if launch_browser:
                    logger.warning('Site uri: %s. Launching it in browser...', launch_url)
                    open_page_in_browser(launch_url)
                else:
                    logger.warning('Site uri: %s.', launch_url)
                if not attach:
                    process.kill()
                    break
            if sentinel_text and sentinel_text in output:
                idle_time_limit_in_sec = 10
        else:
            now = datetime.datetime.now()
            if empty_time is None:
                empty_time = now
            else:
                if (now - empty_time).seconds > idle_time_limit_in_sec:
                    logger.warning('No output for {} seconds, assuming the deployment is done'.format(idle_time_limit_in_sec))
                    if launch_browser:
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


def patch_django_for_azure(cwd):
    requirements_txt = os.path.join(cwd, 'requirements.txt')
    with open(requirements_txt, 'r+') as f:
        existing = f.read()
        if "django-heroku" not in existing:
            f.seek(0)
            f.write(existing + '\n' + 'django-heroku==0.3.1')
            logger.warning('Add "django-heroku==0.3.1" to ' + requirements_txt)

    # retrieve the second tier of the folder and update settings
    manage_py = os.path.join(cwd, 'manage.py')
    setting_file = None
    with open(manage_py, 'r') as f:
        existing = f.read()
        r = re.search('DJANGO_SETTINGS_MODULE.+[\'"](.+?)[\'"]', existing)
        if r:
            r = r.group(1).split('.')
            r[-1] += '.py'
            setting_file = os.path.join(cwd, *r)
            if not os.path.exists(setting_file):
                setting_file = None
    if setting_file:
        with open(setting_file, 'r+') as f:
            existing = f.read()
            if "django_heroku" not in existing:
                f.seek(0)
                f.write(existing + '\n' + 'import django_heroku' + '\n' + 'django_heroku.settings(locals(), test_runner=False)')
                logger.warning('Enable django-heroku in "{}"'.format(setting_file))
    else:
        logger.warning('Could not find the Django settings module to enable django-heroku')


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
