import json
from .dashboardApi import create_annotation


def main(grafana_url, file_path):
    with open(file_path, 'r') as f:
        data = f.read()

    annotation = json.loads(data)
    result = create_annotation(json.dumps(annotation), grafana_url, http_post_headers=None, verify_ssl=None, client_cert=None, debug=None)
    print("create annotation: {0}, status: {1}, msg: {2}".format(annotation['id'], result[0], result[1]))
