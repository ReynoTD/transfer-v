import os
import re
import unicodedata
import PIL.Image
from google import genai
from dotenv import load_dotenv

load_dotenv()

# CATALOGO DE EQUIVALENTES
MAPA_BANCOS = {
    "BANCO AZTECA": "AZTECA",
    "GUARDADITO": "AZTECA",
    "AZTECA": "AZTECA",
    "NU": "NU MEXICO",
    "NU MÉXICO": "NU MEXICO",
    "NU MEXICO": "NU MEXICO",
    "BBVA": "BBVA MEXICO",
    "BBVA MÉXICO": "BBVA MEXICO",
    "BBVA MEXICO": "BBVA MEXICO",
    "COPPEL": "BANCOPPEL",
    "BANCOPPEL": "BANCOPPEL",
    "COMPARTAMOS BANCO": "COMPARTAMOS",
    "COMPARTAMOS": "COMPARTAMOS",
    "MERCADO PAGO": "MERCADO PAGO W",
    "MERCADOPAGO": "MERCADO PAGO W",
    "MERCADO PAGO W": "MERCADO PAGO W",
}

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def normalizar_texto(texto):
    """Devuelve el texto sin acentos, en mayúsculas y sin espacios extra."""
    if not texto:
        return ""
    texto = str(texto).upper().strip()
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto

def estandarizar_banco(nombre_banco):
    """Devuelve el nombre estandarizado del banco"""
    nombre_banco = normalizar_texto(nombre_banco)

    for alias, nombre_estandar in MAPA_BANCOS.items():
        if alias in nombre_banco:
            return nombre_estandar
    return nombre_banco

def extraer_datos_desde_imagen(ruta_imagen):
    """Usa Gemini para extraer los datos relevantes de la imagen de la transferencia."""
    img = PIL.Image.open(ruta_imagen)

    config_v2 = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "fecha": {"type": "STRING", "description": "DD-MM-YYYY"},
                "clave_rastreo": {"type": "STRING"},
                "numero_referencia": {"type": "STRING"},
                "banco_origen": {"type": "STRING"},
                "banco_destino": {"type": "STRING"},
                "monto": {"type": "STRING"},
            },
            "required": [
                "fecha",
                "banco_origen",
                "banco_destino",
                "monto",
            ],
        },
    }

    prompt = """Extrae los datos de la transferencia para Banxico CEP. IMPORTANTE:
    - Solo llena 'clave_rastreo' si el comprobante muestra explícitamente el texto 'Clave de rastreo'.
    - Solo llena 'numero_referencia' si el comprobante muestra explícitamente 'Número de referencia'.
    - No inventes claves de rastreo a partir de otros números del comprobante.
    - Si no existe clave de rastreo, devuelve cadena vacía."""

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=[prompt, img], config=config_v2
    )

    datos = response.parsed
    # Limpieza: Todo a mayúsculas, sin espacios extra y sin símbolos raros
    datos_limpios = {k: normalizar_texto(v) for k, v in datos.items()}

    # Estandarizar bancos usando el mapa de equivalentes
    datos_limpios["banco_origen"] = estandarizar_banco(datos_limpios["banco_origen"])
    datos_limpios["banco_destino"] = estandarizar_banco(datos_limpios["banco_destino"])

    datos_limpios["monto"] = re.sub(
        r"[^\d.]", "", datos_limpios["monto"]
    )  # Solo números y punto decimal
    return datos_limpios
