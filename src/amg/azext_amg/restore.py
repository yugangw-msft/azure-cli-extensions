from .api_checks import main as api_checks
from .create_folder import main as create_folder
from .create_dashboard import main as create_dashboard
from .create_snapshot import main as create_snapshot
from .create_annotation import main as create_annotation
from .create_datasource import main as create_datasource
from glob import glob
import sys
import tarfile
import tempfile
import os
import shutil
import fnmatch
import collections


def restore(grafana_url, archive_file, components, http_headers):
    def open_compressed_backup(compressed_backup):
        try:
            tar = tarfile.open(fileobj=compressed_backup, mode='r:gz')
            return tar
        except Exception as e:
            print(str(e))
            sys.exit(1)

    (status, json_resp, dashboard_uid_support, datasource_uid_support, paging_support) = api_checks(True, grafana_url, http_headers)

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        sys.exit(1)
    else:
        try:
            tarfile.is_tarfile(name=archive_file)
        except IOError as e:
            print(str(e))
            sys.exit(1)
        try:
            tar = tarfile.open(name=archive_file, mode='r:gz')
        except Exception as e:
            print(str(e))
            sys.exit(1)

    # TODO:
    # Shell game magic warning: restore_function keys require the 's'
    # to be removed in order to match file extension names...
    restore_functions = collections.OrderedDict()
    restore_functions['folder'] = create_folder
    restore_functions['dashboard'] = create_dashboard
    restore_functions['snapshot'] = create_snapshot
    restore_functions['annotation'] = create_annotation
    restore_functions['datasource'] = create_datasource

    with tempfile.TemporaryDirectory() as tmpdir:
        tar.extractall(tmpdir)
        tar.close()
        restore_components(grafana_url, restore_functions, tmpdir, components, http_headers)


def restore_components(grafana_url, restore_functions, tmpdir, components, http_headers):

    if components:
        exts = [c[:-1] for c in components]
    else:
        exts = restore_functions.keys()
    if "folder" in exts:  # make "folder" be the first to restore, so dashboards can be positioned under a right folder
        exts.insert(0, exts.pop(exts.index("folder")))

    for ext in exts:
        for file_path in glob('{0}/**/*.{1}'.format(tmpdir, ext), recursive=True):
            print('restoring {0}: {1}'.format(ext, file_path))
            restore_functions[ext](grafana_url, file_path, http_headers)
