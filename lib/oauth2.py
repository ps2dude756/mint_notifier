import json
import requests

class Consumer:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def authorize(self, auth_url, response_type, **kwargs):
        url = '{0}?client_id={1}&response_type={2}'.format(
            auth_url, self.client_id, response_type
        )
        if kwargs:
            url += '&{0}'.format('&'.join(
                ['{0}={1}'.format(key, val) for key, val in kwargs.items()]
            ))
        return 'Go to {0} in a web browser!'.format(url)

    def get_request_token(self, token_url, grant_type, **kwargs):
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': grant_type,
        }
        for key, val in kwargs.items():
            payload[key] = val

        r = requests.post(token_url, data=payload)
        return json.loads(r.text)['refresh_token']

    def get_access_token(self, token_url, refresh_token):
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        r = requests.post(token_url, data=payload)
        return json.loads(r.text)['access_token']

    def api_request_get(self, url, access_token, **kwargs):
        r = requests.get(url, 
            headers={'Authorization': 'Bearer {0}'.format(access_token)},
            params=kwargs
        )
        return json.loads(r.text)

    def api_request_post(self, url, access_token, **kwargs):
        r = requests.post(url, 
            headers={
                'Content-Type':  'application/json',
                'Authorization': 'Bearer {0}'.format(access_token),
            },
            data=json.dumps(kwargs)
        )
        return json.loads(r.text)
