import base64

from email.mime.text import MIMEText

from .oauth2 import Consumer
from .source import Source

AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
MESSAGES_URL = 'https://www.googleapis.com/gmail/v1/users/me/messages'
SEND_URL = 'https://www.googleapis.com/gmail/v1/users/me/messages/send'
TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'

class Google(Source):
    def __init__(
        self, 
        data_file, 
        client_id, 
        client_secret, 
        from_address, 
        header, 
        footer
    ):
        Source.__init__(self, data_file)
        self.consumer = Consumer(client_id, client_secret)
        self.from_address = from_address
        self.header = header
        self.footer = footer
        self.access_token = None

    def setUp(self):
        try:
            refresh_token = self._read_from_file('google')
        except (IOError, ValueError, KeyError):
            refresh_token = None
        if not refresh_token:
            print(
                    self.consumer.authorize(
                            AUTH_URL,
                            'code',
                            redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                            scope='%20'.join(
                                [
                                    'https://mail.google.com/',
                                    'https://www.googleapis.com/auth/gmail.modify',
                                    'https://www.googleapis.com/auth/gmail.compose'
                                ]
                            ),
                            login_hint=self.from_address
                    )
            )
            refresh_token = self.consumer.get_request_token(
                TOKEN_URL,
                'authorization_code',
                code=input(
                    'Please enter the code provided by the website: '
                ),
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            self._write_to_file('google', refresh_token)
        self.access_token = self.consumer.get_access_token(
            TOKEN_URL,
            refresh_token
        )

    def get_first_message_snippet(self):
        messages = self.consumer.api_request_get(MESSAGES_URL, self.access_token)
        first_message = self.consumer.api_request_get('{0}/{1}'.format(MESSAGES_URL, messages['messages'][0]['id']), self.access_token)
        return first_message['snippet']

    def send_message(self, message, to_address):
        msg = MIMEText(self.header + message + self.footer)
        msg['To'] = to_address
        msg['From'] = self.from_address
        raw = base64.urlsafe_b64encode(msg.as_string().encode('utf-8')).decode()
        return self.consumer.api_request_post(
            SEND_URL, 
            self.access_token, 
            raw=raw
        )
