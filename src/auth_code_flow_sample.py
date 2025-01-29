import os
import requests
import webbrowser
import threading
import base64
import time
import dotenv
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
last_refresh = os.getenv("SPOTIFY_LAST_REFRESH")

access_token_event = threading.Event()


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global access_token

        if self.path.startswith("/callback"):
            try:
                code = self.path.split("=")[1].replace("&state", "")
                print(f"\nAUTHORIZATION CODE: {code}")

                access_token = get_access_token(code)
                print(f"\nACCESS TOKEN: {access_token}")

                access_token_event.set()

            except Exception as e:
                print(f"Error: {e}")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization complete. You can close this window now.")

            threading.Thread(target=self.server.shutdown).start()


def get_authorization_code():
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user-read-private user-read-email user-read-playback-state user-modify-playback-state&state=123"

    webbrowser.open(auth_url)

    access_token_event.wait()

    server_thread.join()
    print("\n\n¡Servidor detenido!\n\n")


def get_access_token(code):
    global access_token, refresh_token, last_refresh

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {encode_base64(CLIENT_ID + ':' + CLIENT_SECRET)}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        refresh_token = response.json().get("refresh_token")
        last_refresh = time.time()

        dotenv.set_key(dotenv.find_dotenv(), "SPOTIFY_ACCESS_TOKEN", access_token)
        dotenv.set_key(dotenv.find_dotenv(), "SPOTIFY_REFRESH_TOKEN", refresh_token)
        dotenv.set_key(dotenv.find_dotenv(), "SPOTIFY_LAST_REFRESH", str(last_refresh))

        return access_token

    else:
        print("Error al obtener el token de acceso")
        return None


def get_refresh_token():
    global access_token, refresh_token, last_refresh

    print(f"Refrescar token de acceso: {refresh_token}")

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {encode_base64(CLIENT_ID + ':' + CLIENT_SECRET)}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )

    print(response.json())

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        last_refresh = time.time()

        dotenv.set_key(dotenv.find_dotenv(), "SPOTIFY_ACCESS_TOKEN", access_token)
        dotenv.set_key(dotenv.find_dotenv(), "SPOTIFY_LAST_REFRESH", str(last_refresh))

        return access_token

    else:
        print("Error al renovar el token de acceso")
        return None


def encode_base64(string):
    return base64.b64encode(string.encode()).decode()


def run_server():
    httpd = HTTPServer(("localhost", 8888), CallbackHandler)
    httpd.serve_forever()
    httpd.server_close()


def play_song():
    print("----- REPRODUCIR CANCIÓN -----")

    while True:
        song_info, song_uri = search_song()

        print("\nCanción: ", song_info)
        print("¿Es esta la canción que desea reproducir? (s/n)")
        confirm = input()

        if confirm == "s":
            break

    play = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "uris": [song_uri],
            "position_ms": 0,
        },
    )

    input("\nPresione Enter para continuar...")


def search_song():
    print("----- BUSCAR CANCIÓN -----")
    song_name = input("\nDigite el nombre de la canción: ")
    search_type = "track"

    search_response = requests.get(
        f"https://api.spotify.com/v1/search?q={song_name}&type={search_type}&limit=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if search_response.status_code != 200:
        print(search_response.json())
        raise Exception("Failed to search")

    song_name = search_response.json()["tracks"]["items"][0]["name"]
    song_artist = search_response.json()["tracks"]["items"][0]["artists"][0]["name"]
    song_info = f"{song_name} - {song_artist}"
    song_uri = search_response.json()["tracks"]["items"][0]["uri"]

    return song_info, song_uri


def is_expired_token():
    print(f"Diferencia: {time.time() - float(last_refresh)}")
    return time.time() - float(last_refresh) >= 3600


if __name__ == "__main__":
    if access_token == "None":
        get_authorization_code()

    elif is_expired_token():
        get_refresh_token()

    print(f"Token de acceso: {access_token}")
    play_song()
