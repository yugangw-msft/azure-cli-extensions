import json
from .dashboardApi import create_snapshot


def main(grafana_url, file_path, http_headers):
    with open(file_path, 'r', encoding="utf8") as f:
        data = f.read()

    snapshot = json.loads(data)
    try:
        snapshot['name'] = snapshot['dashboard']['title']
    except KeyError:
        snapshot['name'] = "Untitled Snapshot"

    (status, content) = create_snapshot(json.dumps(snapshot), grafana_url, http_post_headers=http_headers, verify_ssl=None, client_cert=None, debug=None)
    if status == 200:
        print("create snapshot: {0}, status: {1}, msg: {2}".format(snapshot['name'], status, content))
    else:
        print("creating snapshot {0} failed with status {1}".format(snapshot['name'], status))
