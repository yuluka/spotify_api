import os
import requests
import time
from dotenv import load_dotenv
from auth_code_flow import AuthCodeFlow

load_dotenv()

# Base URL for the Spotify API
BASE_URL = os.getenv("BASE_URL")

# Client credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# URI to redirect after authorization
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Token that allows access to the Spotify API
access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")

# Token to refresh the access token without the need for user authorization
refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")

# Last time the access token was refreshed
last_refresh = os.getenv("SPOTIFY_LAST_REFRESH")

authenticator = AuthCodeFlow(
    CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, access_token, refresh_token, last_refresh
)

re_auth = False


def is_expired_token():
    """
    Check if the access token has expired.
    """

    # print(f"Diferencia: {time.time() - float(last_refresh)}")
    return time.time() - float(last_refresh) >= 3600


if access_token == "None" or re_auth:
    print("No hay token de acceso")
    access_token = authenticator.authenticate(re_auth)

elif is_expired_token():
    access_token = authenticator.refresh_token()

# response = requests.post(
#     "https://accounts.spotify.com/api/token",
#     headers={"Content-Type": "application/x-www-form-urlencoded"},
#     data={
#         "grant_type": "client_credentials",
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#     },
# )

# if response.status_code != 200:
#     print(response.json())
#     raise Exception("Failed to get token")
# else:
#     token = response.json()["access_token"]

#     print(f"El token es: {token}")


def search_item(item_type, item_name):
    """
    Search for an item on Spotify and return the result.
    """

    search_response = requests.get(
        f"{BASE_URL}/search?q={item_name}&type={item_type}&limit=1",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    if search_response.status_code != 200:
        print(search_response.json())
        raise Exception("Failed to search")

    search_response = search_response.json()

    # print(search_response)

    item_name = search_response[f"{item_type}s"]["items"][0]["name"]
    item_uri = search_response[f"{item_type}s"]["items"][0]["uri"]

    # If the item is an artist, or playlist, return its name and URI
    if item_type == "artist" or item_type == "playlist":
        return item_name, item_uri

    # If the item is an album, or track, return the item info (artists, item name) and URI
    artists = search_response[f"{item_type}s"]["items"][0]["artists"]
    artist_names = ", ".join([artist["name"] for artist in artists])
    item_info = f"{item_name} - {artist_names}"

    return item_info, item_uri


def play_song():
    """
    Search for a song on Spotify, ask the user if it is the correct song, and play it. Otherwise, repeat the process.
    """

    print("----- REPRODUCIR CANCIÓN -----")

    song_uri = confirm_item("track")

    play = requests.put(
        f"{BASE_URL}/me/player/play",
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


def play_album():
    """
    Search for an album on Spotify, ask the user if it is the correct album, and play it. Otherwise, repeat the process.
    """

    print("----- REPRODUCIR ÁLBUM -----")

    album_uri = confirm_item("album")

    play = requests.put(
        f"{BASE_URL}/me/player/play",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "context_uri": album_uri,
            "offset": {
                "position": 0,
            },
            "position_ms": 0,
        },
    )

    input("\nPresione Enter para continuar...")


def play_playlist():
    """
    Search for a playlist on Spotify, ask the user if it is the correct playlist, and play it. Otherwise, repeat the process.
    """

    print("----- REPRODUCIR PLAYLIST -----")

    choice = input("\n¿Desea reproducir una playlist propia? (s/n) ")

    if choice == "s":
        playlists = get_own_playlists()

        for i, playlist in enumerate(playlists.keys()):
            print(f"{i+1}. {playlist}")

        input_playlist = int(
            input("\nDigite el número de la playlist que desea reproducir: ")
        )

        playlist_uri = playlists[list(enumerate(playlists))[input_playlist - 1][1]]

    else:
        playlist_uri = confirm_item("playlist")

    play = requests.put(
        f"{BASE_URL}/me/player/play",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "context_uri": playlist_uri,
            "offset": {
                "position": 0,
            },
            "position_ms": 0,
        },
    )

    input("\nPresione Enter para continuar...")


def play_artist():
    """
    Search for an artist on Spotify, ask the user if it is the correct artist, and play it. Otherwise, repeat the process.
    """

    print("----- REPRODUCIR ARTISTA -----")

    artist_uri = confirm_item("artist")

    play = requests.put(
        f"{BASE_URL}/me/player/play",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "context_uri": artist_uri,
        },
    )

    input("\nPresione Enter para continuar...")


def play_likes():
    """
    Play the user's liked songs.
    """

    print("----- REPRODUCIR TUS ME GUSTA -----")

    user_id = requests.get(
        f"{BASE_URL}/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    user_id = user_id.json()["id"]

    play = requests.put(
        f"{BASE_URL}/me/player/play",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "context_uri": f"spotify:user:{user_id}:collection",
        },
    )

    try:
        print(play.json())
    except:
        pass

    input("\nPresione Enter para continuar...")


def add_song_to_queue():
    """
    Add a song to the queue.
    """

    print("----- AGREGAR CANCIÓN A LA COLA -----")

    song_uri = confirm_item("track")

    add = requests.post(
        f"{BASE_URL}/me/player/queue?uri={song_uri.replace(':', '%3A')}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    input("\nPresione Enter para continuar...")


def confirm_item(item_type):
    """
    Search for an item on Spotify, ask the user if it is the correct item, and return the URI when it is.
    """

    while True:
        item_name = input(f"\nDigite el nombre del {item_type}: ")
        item_info, item_uri = search_item(item_type, item_name)

        print(f"\n{item_type.capitalize()}: {item_info}")
        print(f"¿Es este el {item_type} que desea reproducir? (s/n)")
        confirm = input()

        if confirm == "s":
            return item_uri


def like_song():
    """
    Like a song.
    """

    print("----- DAR LIKE A UNA CANCIÓN -----")

    current_song_id = get_current_playback()["item"]["id"]

    like = requests.put(
        f"{BASE_URL}/me/tracks?ids={current_song_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "ids": current_song_id,
        },
    )

    input("\nPresione Enter para continuar...")


def get_current_playback():
    """
    Get the current playback.
    """

    playback_state = requests.get(
        f"{BASE_URL}/me/player",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # current_song_uri = playback_state.json()["item"]["uri"]
    # current_song_id = playback_state.json()["item"]["id"]

    return playback_state.json()


def follow_artist():
    """
    Follows the current artist.
    """

    print("----- SEGUIR ARTISTA -----")

    artist_id = get_current_playback()["item"]["artists"][0]["id"]

    follow_response = requests.put(
        f"{BASE_URL}/me/following",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        params={
            "type": "artist",
            "ids": artist_id,
        },
    )

    try:
        print(follow_response.json())
    except:
        pass

    input("\nPresione Enter para continuar...")


def get_current_song_info():
    """
    Get the current song info: name, artists, and duration (mm:ss).
    """

    print("----- INFORMACIÓN DE LA CANCIÓN ACTUAL -----")

    current_playback_info = get_current_playback()

    current_song_name = current_playback_info["item"]["name"]
    current_song_artists = ", ".join(
        [artist["name"] for artist in current_playback_info["item"]["artists"]]
    )

    current_song_duration_ms = current_playback_info["item"]["duration_ms"]
    seconds = current_song_duration_ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60

    print(f"Nombre: {current_song_name}")
    print(f"Artista(s): {current_song_artists}")
    print(f"Duración: {minutes}:{seconds:02d}")

    input("\nPresione Enter para continuar...")


def get_current_queue():
    """
    Get the current queue.
    """

    print("----- COLA ACTUAL -----")

    queue_response = requests.get(
        f"{BASE_URL}/me/player/queue",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    if queue_response.status_code != 200:
        print(queue_response.json())
        raise Exception("Failed to get queue")

    queue_response = queue_response.json()

    queue = queue_response["queue"]

    print(queue)

    queue_names = ""

    for item in queue:
        song_name = item["name"]
        song_artists = ", ".join([artist["name"] for artist in item["artists"]])

        queue_names += f"- {song_name} - {song_artists}\n"

    print(f"\n{queue_names}")

    input("\nPresione Enter para continuar...")


def set_volume():
    """
    Set the volume of the player.
    """

    print("----- AJUSTAR VOLUMEN -----")

    volume_level = input("\nDigite el nivel de volumen (0-100): ")

    set_volume_response = requests.put(
        f"{BASE_URL}/me/player/volume?volume_percent={volume_level if int(volume_level) >= 0 and int(volume_level) <= 100 else 100}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    input("\nPresione Enter para continuar...")


def get_own_playlists():
    """
    Get the user's playlists.
    """

    playlists_response = requests.get(
        f"{BASE_URL}/me/playlists?limit=50",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    if playlists_response.status_code != 200:
        print(playlists_response.json())
        raise Exception("Failed to get playlists")

    playlists_response = playlists_response.json()
    playlists_names = [playlist["name"] for playlist in playlists_response["items"]]
    playlists_uris = [playlist["uri"] for playlist in playlists_response["items"]]

    playlists = dict(zip(playlists_names, playlists_uris))

    return playlists


def show_menu():
    """
    Show the main menu.
    """

    os.system("cls")

    print("Digite la acción que desea realizar:")
    print("1. Buscar canción")
    print("2. Reproducir canción")
    print("3. Reproducir album")
    print("4. Reproducir playlist")
    print("5. Reproducir artista")
    print("6. Reproducir Tus Me Gusta")
    print("7. Agregar canción a la cola")
    print("8. Dar like a una canción")
    print("9. Seguir artista")
    print("10. Obtener información canción actual")
    print("11. Obtener cola actual")
    print("12. Establecer volumen")
    print("0. Salir")

    action = input()

    os.system("cls")

    if action == "1":
        song_info, song_uri = search_item(
            "track", input("Digite el nombre de la canción: ")
        )
        print("\nCanción: ", song_info)
        print("URI de la canción: ", song_uri)
        input("\nPresione Enter para continuar...")

    elif action == "2":
        play_song()

    elif action == "3":
        play_album()

    elif action == "4":
        play_playlist()

    elif action == "5":
        play_artist()

    elif action == "6":
        play_likes()

    elif action == "7":
        add_song_to_queue()

    elif action == "8":
        like_song()

    elif action == "9":
        follow_artist()

    elif action == "10":
        get_current_song_info()

    elif action == "11":
        get_current_queue()

    elif action == "12":
        set_volume()

    elif action == "0":
        print("¡Adiós! :-)")
        return

    show_menu()


show_menu()
