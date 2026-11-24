import os
import httpx
from fastapi import HTTPException

_token_cache = {"access_token": None}

#Trae el token de Twitch
def _get_access_token():
    if _token_cache["access_token"]:
        return _token_cache["access_token"]

    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Credenciales de Twitch no configuradas en el archivo .env")

    url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    response = httpx.post(url)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="No se pudo autenticar con Twitch")

    _token_cache["access_token"] = response.json()["access_token"]
    return _token_cache["access_token"]

#Trae los streamers de Twitch por su login
def get_streamer(login: str):

    client_id = os.getenv("TWITCH_CLIENT_ID")
    token = _get_access_token()

    url = f"https://api.twitch.tv/helix/users?login={login}"
    response = httpx.get(url, headers={"Client-Id": client_id, "Authorization": f"Bearer {token}"})

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Error de la API de Twitch")

    data = response.json().get("data", [])
    if not data:
        raise HTTPException(status_code=404, detail=f"Streamer '{login}' no encontrado en Twitch")

    return data[0]
