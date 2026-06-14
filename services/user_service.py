import json
import os
import re

DATA_FILE = "data/usuarios.json"

def _asegurar_archivo():
    """Crea el archivo de datos y el directorio si no existen."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def guardar_cuenta(user_id, cuenta):
    """Registra o actualiza la cuenta beneficiaria de un usuario."""
    _asegurar_archivo()
    
    # Limpiar cuenta: solo números
    cuenta_limpia = re.sub(r"\D", "", str(cuenta))
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)
    
    user_id_str = str(user_id)
    usuarios[user_id_str] = {"cuenta": cuenta_limpia}
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)
    
    return True

def obtener_cuenta(user_id):
    """Obtiene la cuenta beneficiaria de un usuario. Devuelve None si no existe."""
    _asegurar_archivo()
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)
    
    user_id_str = str(user_id)
    if user_id_str in usuarios:
        return usuarios[user_id_str].get("cuenta")
    
    return None
