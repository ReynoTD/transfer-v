"""Transfer V: VERIFICADOR DE TRANSFERENCIAS INTERBANCARIAS"""

import asyncio
import json
import os
import re
import unicodedata

import PIL.Image
from dotenv import load_dotenv
from google import genai
from playwright.async_api import async_playwright

load_dotenv()  # Carga las variables de entorno desde el archivo .env


# NORMALIZAR TEXTO
def normalizar_texto(texto):
    """Devuelve el texto sin acentos, en mayúsculas y sin espacios extra."""
    texto = texto.upper().strip()
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto


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


def estandarizar_banco(nombre_banco):
    """Devuelve el nombre estandarizado del banco"""
    nombre_banco = normalizar_texto(nombre_banco)

    for alias, nombre_estandar in MAPA_BANCOS.items():
        if alias in nombre_banco:
            return nombre_estandar
    return nombre_banco


# --- 1. CONFIGURACIÓN DE GEMINI ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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
    datos_limpios = {k: normalizar_texto(str(v)) for k, v in datos.items()}

    # Estandarizar bancos usando el mapa de equivalentes
    datos_limpios["banco_origen"] = estandarizar_banco(datos_limpios["banco_origen"])
    datos_limpios["banco_destino"] = estandarizar_banco(datos_limpios["banco_destino"])

    datos_limpios["monto"] = re.sub(
        r"[^\d.]", "", datos_limpios["monto"]
    )  # Solo números y punto decimal
    return datos_limpios


# --- 2. LÓGICA DE PLAYWRIGHT ---
async def consultar_cep(datos):
    """Usa Playwright para la consulta en el portal de Banxico CEP."""
    async with async_playwright() as p:
        # headless=False permite que veas la ventana del navegador
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("--- Navegando a Banxico ---")
        await page.goto("https://www.banxico.org.mx/cep/", wait_until="networkidle")

        if datos.get("clave_rastreo"):
            criterio = "T"
            valor_criterio = datos["clave_rastreo"]
        elif datos.get("numero_referencia"):
            criterio = "R"
            valor_criterio = datos["numero_referencia"]
        else:
            raise ValueError(
                "No se encontró ni Clave de Rastreo ni Número de Referencia en los datos extraídos."
            )

        # 1. Fecha
        await page.evaluate(f"""
            const f = document.querySelector('#input_fecha');
            f.removeAttribute('readonly');
            f.value = '{datos["fecha"]}';
            f.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """)
        print(f"clave_rastreo = [{datos.get('clave_rastreo')}]")
        print(f"numero_referencia = [{datos.get('numero_referencia')}]")
        print(f"criterio = [{criterio}]")
        print(f"valor_criterio = [{valor_criterio}]")

        # 2. Criterio de búsqueda
        await page.select_option('select[id*="input_tipoCriterio"]', value=criterio)
        await page.fill('input[id*="input_criterio"]', valor_criterio)
        await page.wait_for_timeout(1000)
        # 3. Bancos (Emisor y Receptor)
        for selector, valor in [
            ("#input_emisor", datos["banco_origen"]),
            ("#input_receptor", datos["banco_destino"]),
        ]:
            await page.evaluate(f"""
                const select = document.querySelector('{selector}');
                const option = Array.from(select.options).find(opt =>
                    opt.text.toUpperCase().includes('{valor}')
                );
                if (option) {{
                    select.value = option.value;
                    select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)

        # 4. Cuenta y Monto
        await page.fill('input[id*="input_cuenta"]', datos["cuenta_beneficiaria"])
        await page.fill('input[id*="input_monto"]', datos["monto"])

        print("--- Consultando CEP ... ---")
        await page.click("#btn_Consultar")

        # --- PAUSA DE SEGURIDAD PARA DEPURAR ---
        # Esto da 5 segundos para ver la pantalla antes de que se cierre
        await asyncio.sleep(5)

        try:
            await page.wait_for_selector(".styled-table, .info, .alert", timeout=5000)
            if await page.locator(".styled-table").count() > 0:
                print("✅ RESULTADO ENCONTRADO")
            else:
                error_web = await page.locator(".info, .alert").first.inner_text()
                print(f"❌ BANXICO DICE: {error_web.strip().upper()}")
        except TimeoutError:
            print("El proceso tardó demasiado o no hubo respuesta.")

        await browser.close()


# --- 3. FLUJO PRINCIPAL ---
async def main(archivo_imagen):
    """Flujo principal: extrae datos de la imagen, solicita cuenta beneficiaria
    y consulta en Banxico."""
    try:
        datos = extraer_datos_desde_imagen(archivo_imagen)
        # Detectar transferencias internas
        if datos["banco_origen"] == datos["banco_destino"]:
            print(
                "🔄 Transferencia interna detectada. No se puede consultar en Banxico."
            )
            print(json.dumps(datos, indent=2))
            return

        # Solicitar cuenta manual y limpiar cualquier caracter no numérico
        cuenta_input = input("\n👉 Ingrese la CUENTA BENEFICIARIA: ")
        datos["cuenta_beneficiaria"] = re.sub(r"\D", "", cuenta_input)

        print("\n--- DATOS FINALES A ENVIAR ---")
        print(json.dumps(datos, indent=2))
        print("------------------------------\n")

        await consultar_cep(datos)

    except Exception as e:
        print(f"🚨 ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main("comprobante.jpeg"))
