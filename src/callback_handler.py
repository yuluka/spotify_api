import threading
from http.server import BaseHTTPRequestHandler


class CallbackHandler(BaseHTTPRequestHandler):
    """
    Class to handle the callback from the Spotify API.

    It is used to get the authorization code.
    """

    def do_GET(self):
        if self.path.startswith("/callback"):
            try:
                code = self.path.split("=")[1].replace("&state", "")
                print(f"\nAUTHORIZATION CODE: {code}")

                self.server.authenticator.authorization_code = code

                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b"Authorization complete. You can close this window now."
                )

                self.server.authenticator.access_token_event.set()

            except Exception as e:
                print(f"Error: {e}")

            threading.Thread(target=self.server.shutdown).start()
