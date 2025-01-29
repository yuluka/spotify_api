import requests
import webbrowser
import threading
import base64
import time
import dotenv
from callback_handler import CallbackHandler
from http.server import HTTPServer


class AuthCodeFlow:
    """
    Class to handle the authorization code flow.

    It is used to get the authorization code, the access token, and the refresh token.
    """

    def __init__(
        self,
        client_id,
        client_secret,
        redirect_uri,
        access_token=None,
        refresh_token=None,
        last_refresh=None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token_var = refresh_token
        self.last_refresh = last_refresh

        self.authorization_code = None
        self.access_token_event = threading.Event()

    def authenticate(self, re_auth=False):
        """
        Begins the proccess to obtain the access token and returns it.
        """

        print("Autenticando...")

        if self.access_token != "None" and not re_auth:
            print("Token de acceso ya existe")
            return self.access_token

        code = self.get_authorization_code()
        self.access_token = self.get_access_token()

        return self.access_token

    def get_authorization_code(self):
        """
        Opens a web browser to get the authorization code.
        """

        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()

        scopes = [
            "user-read-private",
            "user-read-email",
            "user-read-playback-state",
            "user-read-currently-playing",
            "user-modify-playback-state",
            "user-library-modify",
            "user-library-read",
            "playlist-read-private",
            "user-follow-modify",
        ]

        auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={' '.join(scope for scope in scopes)}&state=123"

        webbrowser.open(auth_url)

        self.access_token_event.wait()

        server_thread.join()
        print("\n\n¡Servidor detenido!\n\n")

        code = self.authorization_code

        return code

    def run_server(self):
        """
        Runs a server to handle the callback from the Spotify API.
        """

        httpd = HTTPServer(("localhost", 8888), CallbackHandler)
        httpd.authenticator = self
        httpd.serve_forever()
        httpd.server_close()

    def get_access_token(self):
        """
        Trades the authorization code for an access token.
        """

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {self.encode_base64(self.client_id + ':' + self.client_secret)}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": self.authorization_code,
                "redirect_uri": self.redirect_uri,
            },
        )

        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            self.refresh_token_var = response.json().get("refresh_token")
            self.last_refresh = time.time()

            # Updates the .env file with the new tokens
            dotenv.set_key(
                dotenv.find_dotenv(), "SPOTIFY_ACCESS_TOKEN", self.access_token
            )
            dotenv.set_key(
                dotenv.find_dotenv(), "SPOTIFY_REFRESH_TOKEN", self.refresh_token_var
            )
            dotenv.set_key(
                dotenv.find_dotenv(), "SPOTIFY_LAST_REFRESH", str(self.last_refresh)
            )

            return self.access_token

        else:
            print("Error al obtener el token de acceso")
            return None

    def refresh_token(self):
        """
        Refreshes the access token using the refresh token.
        """

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {self.encode_base64(self.client_id + ':' + self.client_secret)}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token_var,
            },
        )

        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            last_refresh = time.time()

            # Updates the .env file with the new access token
            dotenv.set_key(
                dotenv.find_dotenv(), "SPOTIFY_ACCESS_TOKEN", self.access_token
            )
            dotenv.set_key(
                dotenv.find_dotenv(), "SPOTIFY_LAST_REFRESH", str(last_refresh)
            )

            return self.access_token

        else:
            print("Error al renovar el token de acceso")
            return None

    def encode_base64(self, string):
        """
        Encodes a string in base64.
        """

        return base64.b64encode(string.encode()).decode()
