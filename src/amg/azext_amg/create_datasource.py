import json
from grafana_backup.dashboardApi import create_datasource


def main(grafana_url, file_path, http_headers):
    with open(file_path, 'r', encoding="utf8") as f:
        data = f.read()

    datasource = json.loads(data)
    result = create_datasource(json.dumps(datasource), grafana_url, http_post_headers=http_headers, verify_ssl=None, client_cert=None, debug=None)
    print("create datasource: {0}, status: {1}, msg: {2}".format(datasource['name'], result[0], result[1]))
