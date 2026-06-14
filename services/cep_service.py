import asyncio
import os
import traceback
from datetime import datetime

from playwright.async_api import async_playwright

from services.config import DEBUG, DEBUG_PAUSE_SECONDS


async def consultar_cep(datos):
    """Usa Playwright para la consulta en el portal de Banxico CEP."""
    resultado = {"exito": False, "mensaje": "Error desconocido", "detalles": None}

    async with async_playwright() as p:
        try:
            # headless=True para producción, False para depuración
            browser = await p.chromium.launch(headless=not DEBUG)
            context = await browser.new_context()
            page = await context.new_page()

            if DEBUG:
                print("\n=== CONSULTA BANXICO ===")
                print(f"Fecha: {datos.get('fecha')}")
                print(f"Banco origen: {datos.get('banco_origen')}")
                print(f"Banco destino: {datos.get('banco_destino')}")
                print(f"Monto: {datos.get('monto')}")
                print(f"Cuenta beneficiaria: {datos.get('cuenta_beneficiaria')}")
                print(f"Clave rastreo: {datos.get('clave_rastreo')}")
                print(f"Referencia: {datos.get('numero_referencia')}")
                print("========================\n")

            await page.goto("https://www.banxico.org.mx/cep/", wait_until="networkidle")

            if datos.get("clave_rastreo"):
                criterio = "T"
                valor_criterio = datos["clave_rastreo"]
            elif datos.get("numero_referencia"):
                criterio = "R"
                valor_criterio = datos["numero_referencia"]
            else:
                resultado["mensaje"] = (
                    "No se encontró ni Clave de Rastreo ni Número de Referencia."
                )
                await browser.close()
                return resultado

            # 1. Fecha
            await page.evaluate(f"""
                const f = document.querySelector('#input_fecha');
                if (f) {{
                    f.removeAttribute('readonly');
                    f.value = '{datos["fecha"]}';
                    f.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)

            # 2. Criterio de búsqueda
            await page.select_option('select[id*="input_tipoCriterio"]', value=criterio)
            await page.fill('input[id*="input_criterio"]', valor_criterio)
            await page.wait_for_timeout(500)

            # 3. Bancos (Emisor y Receptor)
            # Primero seleccionamos el emisor
            if DEBUG:
                print("--- DEBUG: Seleccionando Banco Emisor ---")
            await page.evaluate(f"""
                const select = document.querySelector('#input_emisor');
                if (select) {{
                    const option = Array.from(select.options).find(opt =>
                        opt.text.toUpperCase().includes('{datos["banco_origen"]}')
                    );
                    if (option) {{
                        select.value = option.value;
                        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}
            """)

            # Esperamos a que el receptor se actualice (JS de Banxico)
            if DEBUG:
                print("--- DEBUG: Esperando actualización de Banco Receptor (DOM) ---")

            try:
                await page.wait_for_function(
                    """
                    () => {
                        const select = document.querySelector('#input_receptor');
                        return select && select.options.length > 1 && !select.disabled;
                    }
                """,
                    timeout=5000,
                )
                if DEBUG:
                    print("--- DEBUG: Formulario actualizado correctamente ---")
            except Exception as e:
                if DEBUG:
                    print(
                        f"--- DEBUG: Aviso - Tiempo de espera de actualización agotado o sin cambios: {e} ---"
                    )

            # Ahora seleccionamos el receptor
            if DEBUG:
                print("--- DEBUG: Seleccionando Banco Receptor ---")
            await page.evaluate(f"""
                const select = document.querySelector('#input_receptor');
                if (select) {{
                    const option = Array.from(select.options).find(opt =>
                        opt.text.toUpperCase().includes('{datos["banco_destino"]}')
                    );
                    if (option) {{
                        select.value = option.value;
                        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}
            """)

            # 4. Cuenta y Monto
            await page.fill('input[id*="input_cuenta"]', datos["cuenta_beneficiaria"])
            await page.fill('input[id*="input_monto"]', datos["monto"])

            if DEBUG:
                os.makedirs("debug", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"debug/{timestamp}_antes.png")

            await page.click("#btn_Consultar")

            try:
                # Esperar a que aparezca un resultado o un error
                await page.wait_for_selector(
                    ".styled-table, .info, .alert", timeout=10000
                )

                if await page.locator(".styled-table").count() > 0:
                    resultado["exito"] = True
                    resultado["mensaje"] = "CEP encontrado exitosamente."
                else:
                    error_web = await page.locator(".info, .alert").first.inner_text()
                    resultado["mensaje"] = f"Banxico dice: {error_web.strip()}"
            except Exception:
                resultado["mensaje"] = (
                    "Tiempo de espera agotado o respuesta inesperada de Banxico."
                )

            if DEBUG:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"debug/{timestamp}_resultado.png")
                print("\n=== RESULTADO CEP ===")
                print(f"Exito: {resultado['exito']}")
                print(f"Mensaje: {resultado['mensaje']}")
                print("=====================\n")
                
                if DEBUG_PAUSE_SECONDS > 0:
                    print(f"Pausa de {DEBUG_PAUSE_SECONDS} segundos para inspección (DEBUG activo)...")
                    await asyncio.sleep(DEBUG_PAUSE_SECONDS)

            await browser.close()
        except Exception as e:
            if DEBUG:
                print("\n🚨 ERROR DURANTE LA CONSULTA CEP:")
                traceback.print_exc()
                try:
                    os.makedirs("debug", exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await page.screenshot(path=f"debug/{timestamp}_error.png")
                except:
                    pass
            resultado["mensaje"] = f"Error en la consulta: {str(e)}"

    return resultado
