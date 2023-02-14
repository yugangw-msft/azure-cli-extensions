import json
from .commons import to_python2_and_3_compatible_string
from .dashboardApi import get_folder_id, create_dashboard


def main(grafana_url, file_path, http_headers):
    with open(file_path, 'r', encoding="utf8") as f:
        data = f.read()

    content = json.loads(data)
    content['dashboard']['id'] = None

    payload = {
        'dashboard': content['dashboard'],
        'folderId': get_folder_id(content, grafana_url, http_post_headers=http_headers, verify_ssl=None, client_cert=None, debug=None),
        'overwrite': True
    }

    result = create_dashboard(json.dumps(payload), grafana_url, http_post_headers=http_headers, verify_ssl=None, client_cert=None, debug=None)
    dashboard_title = to_python2_and_3_compatible_string(content['dashboard'].get('title', ''))
    print("create dashboard {0} response status: {1}, msg: {2} \n".format(dashboard_title, result[0], result[1]))
