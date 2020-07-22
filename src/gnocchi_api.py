from time import time
import requests

class AuthException(Exception):
    ''' Raised when the auth token has expired '''
    pass

class GnocchiAPI:
    def __init__(self, url, token, project_id, user_id):
        self.headers = { 
            'X-AUTH-TOKEN': token,
            'Content-Type': 'application/json'
        }

        self.base_url = url
        self.project_id = project_id
        self.user_id = user_id

    def get_metric(self):
        r = requests.get(self.base_url + "/v1/metric", headers=self.headers)
        if r.status_code == 401:
            raise AuthException()
        elif r.status_code // 100 != 2:
            raise Exception('Response status code: %d'%r.status_code)
        
        return r.json()[-1]['id'].encode('ascii', 'ignore')

    def get_metrics_from_resource(self, resource_id):
        """
        Fetch a disctionary {name: uuid} for all metrics in the given resource.

        E.g. {'cpu': <uuid1>, 'memory', <uuid2>}
        """

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
        """
        Returns a list of all resources available.

        Each resource is a dictionary like the following:
        {
            "created_by_project_id": "",
            "created_by_user_id": "admin",
            "creator": "admin",
            "ended_at": null,
            "id": "75c44741-cc60-4033-804e-2d3098c7d2e9",
            "metrics": {
                "cpu": "5d65c35b-99ee-4e04-b203-b13519b20318",
                "memory": "da83c7c4-4a59-4dce-9721-0b8cabc68e11"
            },
            "original_resource_id": "75C44741-CC60-4033-804E-2D3098C7D2E9",
            "project_id": "BD3A1E52-1C62-44CB-BF04-660BD88CD74D",
            "revision_end": null,
            "revision_start": "2018-05-10T12:28:36.033995+00:00",
            "started_at": "2018-05-10T12:28:36.033902+00:00",
            "type": "generic",
            "user_id": "BD3A1E52-1C62-44CB-BF04-660BD88CD74D"
        }
        """

        r = requests.get(self.base_url + '/v1/resource/generic', headers=self.headers)
        
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:
            raise AuthException()
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
        elif r.status_code == 401:
            raise AuthException()
        else:
            print("Error during get_measures: ", r.status_code)
            print("URL: ", r.url)
            print("Request Headers: ", r.request.headers)
            print("Response Headers: ", r.headers)
            print(r.text)
            return None
