# Transfer V - Verificador de Transferencias Interbancarias (V1)

**Transfer V** es una solución automatizada que integra inteligencia artificial y automatización web para verificar la validez de transferencias interbancarias en México a través de un Bot de Telegram.

El sistema utiliza **Gemini** para extraer datos de comprobantes (vouchers), **Playwright** para consultar el portal CEP (Comprobante Electrónico de Pago) de Banxico y **Telegram** como interfaz de usuario.

---

## Características principales

- 🤖 **Bot de Telegram:** Interfaz amigable para registrar cuentas y enviar comprobantes.
- 🧠 **IA con Gemini:** Extracción automática y precisa de datos desde imágenes de transferencias.
- 🌐 **Automatización con Playwright:** Consulta automática en el portal oficial de Banxico CEP.
- 💾 **Persistencia de Usuarios:** Registro y guardado de cuenta beneficiaria por usuario mediante JSON.
- 🛠️ **Modo Debug:** Herramientas integradas para diagnóstico y visualización del proceso.
- 🏗️ **Arquitectura Modular:** Separación clara entre servicios de IA, automatización y gestión de usuarios.

---

## Estructura del proyecto

```text
transfer-v/
│
├── bot.py                  # Punto de entrada para el Bot de Telegram
├── main.py                 # Orquestador de la lógica de negocio
│
├── services/               # Módulos de servicios especializados
│   ├── gemini_service.py   # Extracción de datos con Google Gemini
│   ├── cep_service.py      # Consulta automatizada en Banxico
│   ├── user_service.py     # Gestión de persistencia de usuarios
│   └── config.py           # Configuración centralizada y Debug Mode
│
├── data/                   # Almacenamiento de datos persistentes
│   └── usuarios.json       # Base de datos simple de usuarios y cuentas
│
├── temp/                   # Archivos temporales
│   └── imagenes/           # Imágenes descargadas temporalmente para proceso
│
├── debug/                  # Capturas de pantalla generadas en modo DEBUG
│
├── README.md               # Documentación del proyecto
├── requirements.txt        # Dependencias de Python
├── .env.example            # Plantilla de variables de entorno
└── .gitignore              # Archivos ignorados por Git
```

---

## Requisitos

- **Python 3.10** o superior.
- **API Key de Gemini:** Obtener en [Google AI Studio](https://aistudio.google.com/).
- **Telegram Bot Token:** Obtener mediante [@BotFather](https://t.me/botfather).
- **Navegador Chromium:** Instalado automáticamente mediante Playwright.

---

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/ReynoTD/transfer-v.git
   cd transfer-v
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Instalar navegador para Playwright:**
   ```bash
   playwright install chromium
   ```

---

## Configuración

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```env
GEMINI_API_KEY=tu_api_key_de_gemini
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
DEBUG=false
DEBUG_PAUSE_SECONDS=0
```

### Variables de Entorno:
- `GEMINI_API_KEY`: Clave para acceder a los modelos de IA de Google.
- `TELEGRAM_BOT_TOKEN`: Token para conectar el script con tu bot de Telegram.
- `DEBUG`: Establecer en `true` para ver el navegador Playwright y logs detallados.
- `DEBUG_PAUSE_SECONDS`: Segundos que el navegador permanecerá abierto tras la consulta (solo en modo DEBUG).

---

## Comandos del Bot

### `/start`
Muestra el mensaje de bienvenida e instrucciones iniciales.

### `/cuenta <número_de_cuenta>`
Registra o actualiza tu cuenta beneficiaria (18 dígitos CLABE o número de tarjeta). Esta cuenta será utilizada para todas tus verificaciones futuras.
*Ejemplo:* `/cuenta 123456789012345678`

---

## Flujo de Trabajo

1. **Registro:** El usuario registra su cuenta beneficiaria una sola vez.
2. **Envío:** El usuario envía una fotografía del comprobante de transferencia al bot.
3. **Descarga:** El bot descarga la imagen de forma segura en la carpeta `temp/`.
4. **Extracción (IA):** Gemini analiza la imagen y extrae: fecha, bancos, monto y clave de rastreo.
5. **Consulta (Web):** Playwright abre el portal de Banxico e ingresa los datos automáticamente.
6. **Respuesta:** El bot envía al usuario el resultado de la verificación y los datos extraídos.
7. **Limpieza:** Se elimina la imagen temporal para proteger la privacidad.

---

## Modo Debug

Activar `DEBUG=true` permite:
- **Navegador Visible:** Observar en tiempo real cómo Playwright llena el formulario en Banxico.
- **Capturas de Diagnóstico:** Generación automática de imágenes en `debug/` antes y después de la consulta.
- **Logs Extendidos:** Visualización en consola de los datos extraídos por Gemini y la respuesta cruda de Banxico.
- **Trazabilidad:** Tracebacks completos en caso de errores en la automatización.

---

## Ejemplo de Uso (Telegram)

1. **Usuario:** `/start`
2. **Bot:** `Bot activo. Registra tu cuenta con /cuenta...`
3. **Usuario:** `/cuenta 123456789012345678`
4. **Bot:** `Cuenta registrada correctamente.`
5. **Usuario:** *[Envía foto del voucher]*
6. **Bot:** `Procesando comprobante...`
7. **Bot:** 
   ```text
   ✅ Verificación completada
   CEP encontrado exitosamente.

   Datos extraídos:
   📅 Fecha: 25-05-2026
   💰 Monto: 1300.00
   🏦 Origen: BBVA MEXICO
   🏦 Destino: BANAMEX
   🔢 Rastreo: MBAN01002605250068386019
   ```

---

## Limitaciones Vigentes

- **Transferencias Internas:** Banxico CEP solo registra transferencias entre bancos distintos (SPEI). Las transferencias entre cuentas del mismo banco no se pueden verificar aquí.
- **Calidad de Imagen:** La precisión de la extracción depende de que los datos en la imagen sean legibles.
- **Disponibilidad:** El servicio depende de la disponibilidad operativa del portal de Banxico y de la API de Gemini.

---

## Tecnologías Utilizadas

- **Python 3.10+**
- **Google Gemini API** (IA Generativa)
- **Playwright** (Automatización Web)
- **python-telegram-bot** (Interfaz de Chat)
- **Pillow** (Procesamiento de Imágenes)
- **python-dotenv** (Gestión de Configuración)

---

## Próximas Funcionalidades (Roadmap)

- [ ] Soporte para múltiples cuentas por usuario (etiquetas como PRINCIPAL, TRABAJO).
- [ ] Historial de verificaciones realizadas.
- [ ] Migración a base de datos SQL (SQLite/PostgreSQL).
- [ ] Despliegue mediante Docker.
- [ ] Panel administrativo para métricas de uso.
- [ ] Soporte para otros tipos de comprobantes dinámicos.
