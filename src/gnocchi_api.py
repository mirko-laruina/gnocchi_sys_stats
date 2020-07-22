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
            r = requests.post(self.base_url + '/v1/resource/generic', 
                    headers=self.headers, 
                    json={
                        "id": resource_id,
                        "project_id": self.project_id,
                        "user_id": self.user_id,
                        "metrics": {
                            "cpu": {
                                "archive_policy_name": "high"
                            },
                            "memory": {
                                "archive_policy_name": "high"
                            }
                        }
                    } 
            )
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

    def list_resources(self):
        r = requests.get(self.base_url + '/v1/resource/generic', headers=self.headers)
        if r.status_code == 200:
            return r.json()
        else:
            print("Error during list_resources: ", r.status_code)
            print("URL: ", r.url)
            print(r.text)
            return None

    def get_measures(self, metric, **kwargs):
        """
        Gets measures for the given metric.

        Positional parameters:
         - metric: str
            ID of the metric

        Keyword parameters:
         - granularity: int
            Return only measures at the given granularity
         - resample: int
            Resample and aggregate on the given granularity
         - start: floating number (UNIX epoch) or an ISO8601 formated timestamp
            Return all measures after the given time
        """
        r = requests.get(self.base_url + '/v1/metric/' + metric +'/measures', params=kwargs, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        else:
            print("Error during get_measures: ", r.status_code)
            print("URL: ", r.url)
            print("Request Headers: ", r.request.headers)
            print("Response Headers: ", r.headers)
            print(r.text)
            return None
