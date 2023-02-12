import os
import random
import string
from .dashboardApi import search_snapshot, get_snapshot
from .commons import print_horizontal_line, save_json


def main(grafana_url, backup_dir, timestamp):
    folder_path = '{0}/snapshots/{1}'.format(backup_dir, timestamp)
    'snapshots_{0}.txt'.format(timestamp)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    get_all_snapshots_and_save(folder_path, grafana_url, http_get_headers=None, verify_ssl=None, client_cert=None, debug=None, pretty_print=None)
    print_horizontal_line()


def save_snapshot(file_name, snapshot_setting, folder_path, pretty_print):
    file_name = file_name.replace('/', '_')
    random_suffix = "".join(random.choice(string.ascii_letters) for _ in range(6))
    file_path = save_json(file_name + "_" + random_suffix, snapshot_setting, folder_path, 'snapshot', pretty_print)
    print("snapshot:{0} is saved to {1}".format(file_name, file_path))


def get_single_snapshot_and_save(snapshot, grafana_url, http_get_headers, verify_ssl, client_cert, debug, folder_path, pretty_print):
    (status, content) = get_snapshot(snapshot['key'], grafana_url, http_get_headers, verify_ssl, client_cert, debug)
    if status == 200:
        save_snapshot(snapshot['name'], content, folder_path, pretty_print)
    else:
        print("getting snapshot {0} failed with {1}".format(snapshot['name'], status))


def get_all_snapshots_and_save(folder_path, grafana_url, http_get_headers, verify_ssl, client_cert, debug, pretty_print):
    status_code_and_content = search_snapshot(grafana_url, http_get_headers, verify_ssl, client_cert, debug)
    if status_code_and_content[0] == 200:
        snapshots = status_code_and_content[1]
        print("There are {0} snapshots:".format(len(snapshots)))
        for snapshot in snapshots:
            print(snapshot)
            get_single_snapshot_and_save(snapshot, grafana_url, http_get_headers, verify_ssl, client_cert, debug, folder_path, pretty_print)
    else:
        print("query snapshot failed, status: {0}, msg: {1}".format(status_code_and_content[0],
                                                                    status_code_and_content[1]))
