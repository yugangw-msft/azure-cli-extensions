import json
from .dashboardApi import create_folder


def main(grafana_url, file_path):
    with open(file_path, 'r') as f:
        data = f.read()

    folder = json.loads(data)
    result = create_folder(json.dumps(folder), grafana_url, http_post_headers=None, verify_ssl=None, client_cert=None, debug=None)
    print("create folder {0}, status: {1}, msg: {2}\n".format(folder.get('title', ''), result[0], result[1]))
