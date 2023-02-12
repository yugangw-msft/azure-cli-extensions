from .api_checks import main as api_checks
from .save_dashboards import main as save_dashboards
from .save_folders import main as save_folders
from .save_snapshots import main as save_snapshots
from .save_annotations import main as save_annotations
from .archive import main as archive
import sys
import datetime


def save(grafana_url, backup_dir, components, http_headers):
    arg_components = components

    backup_functions = {'dashboards': save_dashboards,
                        'folders': save_folders,
                        'snapshots': save_snapshots,
                        'annotations': save_annotations}

    (status, json_resp, dashboard_uid_support, datasource_uid_support, paging_support) = api_checks(True, grafana_url, http_headers)

    timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M')

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        print("server status is not ok: {0}".format(json_resp))
        sys.exit(1)

    if components:
        # Backup only the components that provided via an argument
        for backup_function in components:
            backup_functions[backup_function](grafana_url, backup_dir, timestamp)
    else:
        # Backup every component
        for backup_function in backup_functions.keys():
            backup_functions[backup_function](grafana_url, backup_dir, timestamp)

    archive(backup_dir, timestamp)
