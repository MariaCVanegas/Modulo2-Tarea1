from fastapi import HTTPException


def get_user_or_404(cursor, user_id: int):
    """Busca un usuario por ID. Si no existe, lanza un error 404 automáticamente.
    Se reutiliza en todos los endpoints que necesitan un usuario específico.
    """
    # %s evita SQL injection — nunca interpolar valores directamente en el query
    cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user[0], "username": user[1], "email": user[2]}
