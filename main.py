import json

from services.cep_service import consultar_cep
from services.config import DEBUG
from services.gemini_service import extraer_datos_desde_imagen


async def verificar_transferencia(ruta_imagen: str, cuenta_beneficiaria: str):
    """
    Orquestador principal para la verificación de transferencias.
    1. Extrae datos de la imagen con Gemini.
    2. Detecta si es transferencia interna.
    3. Consulta CEP en Banxico.
    """
    try:
        # 1. Extracción de datos
        datos = extraer_datos_desde_imagen(ruta_imagen)

        # 2. Agregar cuenta beneficiaria
        datos["cuenta_beneficiaria"] = cuenta_beneficiaria

        if DEBUG:
            print("\n=== DATOS EXTRAIDOS ===")
            print(json.dumps(datos, indent=2, ensure_ascii=False))
            print("======================\n")

        # 3. Detectar transferencias internas
        if datos["banco_origen"] == datos["banco_destino"]:
            return {
                "exito": False,
                "mensaje": f"Transferencia interna detectada ({datos['banco_origen']}). No se puede consultar en Banxico CEP.",
                "datos_extraidos": datos,
            }

        # 4. Consultar CEP
        resultado_cep = await consultar_cep(datos)

        return {
            "exito": resultado_cep["exito"],
            "mensaje": resultado_cep["mensaje"],
            "datos_extraidos": datos,
        }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"Error en el proceso de verificación: {str(e)}",
        }


if __name__ == "__main__":
    # Prueba local simple
    # Asegúrate de que la ruta de la imagen sea correcta para tu entorno
    # EJEMPLO:
    # IMAGEN_PRUEBA = "images/voucher.jpeg"
    # CUENTA_PRUEBA = "123456789012345678"

    # if os.path.exists(IMAGEN_PRUEBA):
    #     resultado = asyncio.run(verificar_transferencia(IMAGEN_PRUEBA, CUENTA_PRUEBA))
    #     print(json.dumps(resultado, indent=2, ensure_ascii=False))
    # else:
    #     print(f"No se encontró la imagen de prueba en {IMAGEN_PRUEBA}")

    print(
        "Módulo listo. Ejecuta verificar_transferencia() desde tu bot o script de pruebas."
    )
