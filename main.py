from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from configuration.connections import get_db_connection
from helpers import get_user_or_404
from services.twitch_service import get_streamer

app = FastAPI(
    title="API Streamers - Tarea 1",
    description="API REST para gestionar usuarios y sus streamers favoritos de Twitch.",
    version="1.0.0",
)


# --------------------------------- #
# ------------ MODELOS ------------ #
# --------------------------------- #
# Los modelos de Pydantic validan automáticamente los datos que llegan en cada request.
# Si un campo es inválido, FastAPI rechaza, la petición antes de que llegue al endpoint, sin necesidad de validar manualmente.

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100, examples=["Maria"])
    email: EmailStr = Field(..., examples=["maria@example.com"])

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = Field(default=None)

class PreferenceCreate(BaseModel):
    streamer: str = Field(..., min_length=1, examples=["ibai"])
    category: str | None = Field(default=None, examples=["MOBA"])


# --------------------------------- #
# ------------ USUARIOS ----------- #
# --------------------------------- #

@app.get("/users")
async def list_users():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = [{"id": row[0], "username": row[1], "email": row[2]} for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return users


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    db = get_db_connection()
    cursor = db.cursor()
    user = get_user_or_404(cursor, user_id)
    cursor.close()
    db.close()
    return user


@app.post("/users", status_code=201)
async def create_user(user: UserCreate):
    db = get_db_connection()
    cursor = db.cursor()

    # Verificar que el email no esté registrado
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    cursor.execute(
        "INSERT INTO users (username, email) VALUES (%s, %s)",
        (user.username, user.email),
    )
    db.commit()
    new_id = cursor.lastrowid
    cursor.close()
    db.close()
    return JSONResponse(content={"id": new_id, "username": user.username, "email": user.email}, status_code=201)


@app.patch("/users/{user_id}")
async def update_user(user_id: int, data: UserUpdate):
    db = get_db_connection()
    cursor = db.cursor()

    # Verificar que el usuario existe
    get_user_or_404(cursor, user_id)

    changes = data.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    fields = ", ".join(f"{key} = %s" for key in changes)
    values = list(changes.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {fields} WHERE id = %s", values)
    db.commit()

    updated_user = get_user_or_404(cursor, user_id)
    cursor.close()
    db.close()
    return updated_user


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    db = get_db_connection()
    cursor = db.cursor()

    # Verificar que el usuario existe antes de borrar
    get_user_or_404(cursor, user_id)

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    cursor.close()
    db.close()


# --------------------------------- #
# --------- PREFERENCIAS ---------- #
# --------------------------------- #

@app.get("/users/{user_id}/preferences")
async def get_preferences(user_id: int):
    db = get_db_connection()
    cursor = db.cursor()

    # Verificar que el usuario existe
    get_user_or_404(cursor, user_id)

    cursor.execute(
        "SELECT streamer, category FROM preferences WHERE user_id = %s", (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Este usuario no tiene preferencias guardadas")
    return {"user_id": user_id, "streamer": row[0], "category": row[1]}


@app.put("/users/{user_id}/preferences", status_code=201)
async def save_preferences(user_id: int, preference: PreferenceCreate):
    db = get_db_connection()
    cursor = db.cursor()

    # Verificar que el usuario existe
    get_user_or_404(cursor, user_id)

    # Reemplazar preferencia existente si ya tiene una
    cursor.execute("DELETE FROM preferences WHERE user_id = %s", (user_id,))
    cursor.execute(
        "INSERT INTO preferences (user_id, streamer, category) VALUES (%s, %s, %s)",
        (user_id, preference.streamer, preference.category),
    )
    db.commit()
    cursor.close()
    db.close()
    return {"user_id": user_id, "streamer": preference.streamer, "category": preference.category}


@app.delete("/users/{user_id}/preferences", status_code=204)
async def delete_preferences(user_id: int):
    db = get_db_connection()
    cursor = db.cursor()

    get_user_or_404(cursor, user_id)

    cursor.execute("DELETE FROM preferences WHERE user_id = %s", (user_id,))
    db.commit()
    cursor.close()
    db.close()


# --------------------------------- #
# ------------ TWITCH ------------- #
# --------------------------------- #

@app.get("/twitch/streamers/{login}")
async def get_twitch_streamer(login: str):
    return get_streamer(login)
