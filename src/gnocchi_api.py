from time import time
import requests

class AuthException(Exception):
    ''' Raised when the auth token has expired '''
    pass

class GnocchiAPI:
    def __init__(self, url, token):
        self.headers = { 
            'X-AUTH-TOKEN': token,
            'Content-Type': 'application/json'
        }

        self.base_url = url

    def get_metric(self):
        r = requests.get(self.base_url + "/v1/metric", headers=self.headers)
        if r.status_code == 401:
            raise AuthException()
        elif r.status_code // 100 != 2:
            raise Exception('Response status code: %d'%r.status_code)
        
        return r.json()[-1]['id'].encode('ascii', 'ignore')

    def get_metrics_from_resource(self, resource_id):
        r = requests.get(self.base_url + '/v1/resource/generic/' + resource_id, headers=self.headers)
        if r.status_code == 404:
            # we need to create the resource
            r = requests.post(self.base_url + '/v1/resource/generic', headers=self.headers, json={
                    "id": resource_id,
                    "project_id": '3d22f640-84db-40ce-af49-44468443234f',
                    "user_id": '3d22f640-84db-40ce-af49-44468443234f',
                    "metrics": {
                        "cpu": {
                            "archive_policy_name": "high"
                        },
                        "memory": {
                            "archive_policy_name": "high"
                        }
                    }
                } )
        elif r.status_code == 401:
            raise AuthException()
        elif r.status_code // 100 != 2:
            raise Exception('Response status code: %d'%r.status_code)

        return r.json()['metrics']

    def send_measure(self, metric_id, value, timestamp=None):
        # Gnocchi returns ISO 8601 timestamps, but accepts different formats. Unix epoch is OK
        if timestamp == None:
            timestamp = time()
        
        r = requests.post(
            self.base_url+"/v1/metric/"+metric_id+"/measures",
            headers=self.headers,
            json=[{
                "timestamp": timestamp,
                "value": value
                }]
            )
        
        if r.status_code == 401:
            raise AuthException()
        elif r.status_code // 100 != 2:
            raise Exception('Response status code: %d'%r.status_code)
