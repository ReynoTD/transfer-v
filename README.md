# Transfer V - Verificador de Transferencias Interbancarias

Script en Python que permite verificar transferencias bancarias mediante el portal CEP (Comprobante Electrónico de Pago) de Banxico.

## Características

- Extracción automática de datos desde un comprobante utilizando Gemini.
- Normalización y estandarización de la información obtenida.
- Consulta automática del portal CEP de Banxico mediante Playwright.
- Verificación de la existencia de la transferencia en el sistema de Banxico.

## Requisitos

- Python 3.10 o superior
- API Key de Gemini
- Google Chrome o Chromium

## Instalación

Clona el repositorio:

```bash
git clone <url-del-repositorio>
cd transfer-v
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Instala los navegadores de Playwright:

```bash
playwright install
```

## Configuración

Crea un archivo `.env` en la raíz del proyecto:

```env
GEMINI_API_KEY=coloca_tu_api_key_aqui
```

## Flujo de trabajo

1. El usuario proporciona una imagen del comprobante.
2. Gemini analiza la imagen y extrae los datos relevantes.
3. La información es normalizada y validada.
4. Se solicita la cuenta beneficiaria.
5. El sistema consulta automáticamente el portal CEP de Banxico.
6. Se informa si la transferencia fue encontrada.

## Uso

Coloca la imagen del comprobante dentro de la carpeta del proyecto.

En `main.py`, especifica el nombre de la imagen:

```python
if __name__ == "__main__":
    asyncio.run(main("comprobante.jpeg"))
```

Ejecuta el programa:

```bash
python main.py
```

## Ejemplo de ejecución

```bash
$ python main.py

👉 Ingrese la CUENTA BENEFICIARIA: 123456789012345678

--- DATOS FINALES A ENVIAR ---

--- Navegando a Banxico ---

--- Consultando CEP ... ---

✅ RESULTADO ENCONTRADO
```

## Ejemplo de salida

```json
{
  "fecha": "01-06-2026",
  "clave_rastreo": "ABC123456",
  "banco_origen": "BBVA MEXICO",
  "banco_destino": "NU MEXICO",
  "monto": "1500.00"
}
```

Si la transferencia es localizada correctamente en CEP, se mostrará:

```bash
✅ RESULTADO ENCONTRADO
```

## Limitaciones

- Las transferencias internas (mismo banco origen y destino) no pueden consultarse mediante CEP.
- La cuenta beneficiaria se solicita manualmente antes de realizar la consulta.
- La precisión de la extracción depende de la calidad de la imagen proporcionada.
- Gemini puede interpretar incorrectamente algunos datos en comprobantes con baja calidad o formatos poco comunes.
- El navegador se ejecuta en modo visible (`headless=False`) para facilitar la depuración.

## Tecnologías utilizadas

- Python
- Gemini API
- Playwright
- Pillow
- python-dotenv

## Próximas funcionalidades

- Refactorización para convertir el proyecto en un bot.
- Ejecución sin interacción por consola.
- Integración con Telegram.
- Recepción de imágenes enviadas por los usuarios.
- Procesamiento automático de consultas.
