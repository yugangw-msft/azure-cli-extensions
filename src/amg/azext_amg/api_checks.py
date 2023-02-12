from .dashboardApi import health_check, auth_check


def main(api_health_check, grafana_url):
    if api_health_check:
        (status, json_resp) = health_check(grafana_url, False, True, None, None)
        if not status == 200:
            return (status, json_resp, None, None, None)

    (status, json_resp) = auth_check(grafana_url, None, True, None, False)
    if not status == 200:
        return (status, json_resp, None, None, None)

    if status == 200:
        print("[Pre-Check] Server status is 'OK' !!")
    else:
        print("[Pre-Check] Server status is NOT OK !!: {0}".format(json_resp))

    return (status, json_resp, True, True, True)
