from fastapi import HTTPException

#Esta funcion se reutilizará en todos los endpoints que necesiten buscar un usuario especifico por id, si no lo encuentra arroja el error
def get_user_or_404(cursor, user_id: int):
    cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user[0], "username": user[1], "email": user[2]}
