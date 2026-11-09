# validacion-pdf

Microservicio FastAPI del proyecto `microservicios-pdf` responsable de validar
archivos PDF recibidos en Base64. Está alineado con el contrato compartido
`microservicios-pdf` v1.4.0 (en el repo `integracion`, `CONTRATO.md`).

## Responsabilidad

El servicio recibe el contenido de un archivo PDF codificado en Base64 y
determina si puede continuar hacia los siguientes microservicios del flujo.

Acciones que realiza:

- Recibir `archivo_base64` y `nombre`.
- Decodificar el contenido Base64.
- Validar que el contenido no esté vacío.
- Validar la firma `%PDF`.
- Validar que el PDF esté completo (marcador `%%EOF`).
- Validar que el PDF no esté protegido con contraseña.
- Validar el tamaño máximo configurado.
- Informar el tamaño recibido en bytes.
- Propagar `X-Correlation-ID` y registrarlo en cada línea de log.
- Exponer un healthcheck.

## Responsabilidades excluidas

Este microservicio no:

- Extrae texto.
- Calcula checksum.
- Persiste el archivo binario.
- Persiste documentos o resultados.
- Usa MongoDB.
- Usa Redis.
- Coordina el flujo entre microservicios.
- Accede a otros microservicios.

La coordinación corresponde al orquestador; la extracción y la persistencia
corresponden a sus respectivos microservicios.

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/validar` | Valida un PDF enviado en Base64. |
| `GET` | `/health` | Healthcheck del servicio. |

La documentación interactiva queda disponible en
`http://localhost:8000/docs` cuando el servicio está levantado.

## Contrato de validación

### Request

```json
{
  "archivo_base64": "JVBERi0xLjQK...",
  "nombre": "contrato.pdf"
}
```

`archivo_base64` y `nombre` son obligatorios. Se aceptan espacios y saltos de
línea dentro del Base64 (por ejemplo, la salida del comando `base64`).

### Response exitosa

HTTP `200`:

```json
{
  "valido": true,
  "nombre": "contrato.pdf",
  "tamano_bytes": 245760
}
```

### Response de error

Todos los errores (de negocio, de schema y no previstos) utilizan el formato
común:

```json
{
  "valido": false,
  "error": {
    "code": "PDF_TOO_LARGE",
    "message": "El archivo supera el tamaño máximo permitido",
    "details": {
      "max_size_bytes": 5242880,
      "received_size_bytes": 7340032
    },
    "correlation_id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
  }
}
```

### Códigos de error

| Código | HTTP | Descripción |
| --- | ---: | --- |
| `PDF_INVALID` | `422` | Base64 inválido, contenido vacío, archivo que no es PDF o PDF protegido con contraseña (este último con `details.reason = "protegido_con_contrasena"`). |
| `PDF_TOO_LARGE` | `413` | El tamaño supera `PDF_MAX_SIZE_MB`. |
| `PDF_CORRUPTED` | `422` | El contenido comienza como PDF, pero no tiene el marcador `%%EOF` (archivo truncado) o PyMuPDF no lo puede abrir. |
| `VALIDATION_ERROR` | `400` | El request no cumple el schema de entrada (falta un campo, campo vacío, body que no es JSON). |
| `INTERNAL_ERROR` | `500` | Error interno no previsto. También devuelve el `correlation_id`. |

## Correlation ID

El servicio propaga la cabecera `X-Correlation-ID`:

- Si la petición trae la cabecera, conserva el valor recibido.
- Si no la trae, genera un identificador UUID.
- El identificador se devuelve en la cabecera de la respuesta.
- En las respuestas de error también aparece como `error.correlation_id`.

## Logs (12-Factor XI)

Los logs van a `stdout`; la aplicación no escribe archivos. La configuración está
en [`logging.json`](logging.json), en la raíz del repo (formato `dictConfig`), y
el nivel sale de `LOG_LEVEL` (contrato `microservicios-pdf` 1.2.0). Cada línea
lleva fecha, nivel, logger y `correlation_id` (`-` fuera de una request), así que
`docker compose logs` alcanza para seguir una request por todos los servicios:

```text
INFO validacion_pdf correlation_id=- servicio iniciado
INFO app.services.validation_service correlation_id=demo-1 pdf valido tamano_bytes=10652
INFO validacion_pdf correlation_id=demo-1 method=POST path=/validar status=200 duracion_ms=1.4
WARNING validacion_pdf correlation_id=demo-2 code=PDF_INVALID status=422 message=El archivo no es un PDF válido
```

| Nivel | Qué registra este servicio |
| --- | --- |
| `INFO` | Cada request (método, ruta, status y duración), PDF aceptado con su tamaño, inicio y apagado. |
| `WARNING` | Rechazos del contrato (`PDF_INVALID`, `PDF_TOO_LARGE`, `PDF_CORRUPTED`, `VALIDATION_ERROR`) con su `code`. |
| `ERROR` | Error no previsto (`INTERNAL_ERROR`), con traceback. |

**No se registran** el Base64, el contenido del archivo ni su nombre (puede tener
datos personales); hay un test que lo verifica. El access log propio de uvicorn
está desactivado en la imagen porque lo registra la app con el `correlation_id`.

## Finalización segura (12-Factor IX)

La imagen corre uvicorn como PID 1 con `--timeout-graceful-shutdown 30`. Ante
`SIGTERM` (`docker stop`) deja de aceptar conexiones, termina las validaciones en
curso, ejecuta el cierre del `lifespan` (`apagado iniciado` / `apagado completo`)
y sale con código 0. Probado con la imagen `1.0.2`:
`docker inspect --format '{{.State.ExitCode}}'` → `0`.

Ejemplo:

```bash
curl -i http://localhost:8000/health \
  -H "X-Correlation-ID: prueba-validacion-001"
```

## Configuración

Copiar `.env.example` como `.env` cuando se necesite configurar el entorno:

```bash
cp .env.example .env
```

| Variable | Ejemplo | Descripción |
| --- | --- | --- |
| `PDF_MAX_SIZE_MB` | `5` | Tamaño máximo permitido del PDF en megabytes. |
| `APP_NAME` | `validacion-pdf` | Nombre de la aplicación. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` o `ERROR` (opcional). Otro valor impide arrancar. |

El archivo `.env` no debe versionarse.

### Configuración desde Consul (contrato 1.6.0)

Con `CONSUL_ENABLED=true`, las variables de la tabla salen del KV de Consul, bajo
`config/validacion-pdf/` (por ejemplo `config/validacion-pdf/PDF_MAX_SIZE_MB`), y tienen
prioridad sobre el entorno. Del entorno solo llega cómo conectarse a Consul:
`CONSUL_ENABLED`, `CONSUL_HTTP_ADDR` y `CONSUL_HTTP_TOKEN_FILE` (el token, como Docker
secret). `CONSUL_SERVICE_ADDRESS` y `CONSUL_SERVICE_PORT` también pueden venir del KV.

- Las claves las carga el servicio `consul-config` del compose de integración, desde
  `integracion/env/validacion.env`.
- Si no hay claves bajo `config/validacion-pdf/` o Consul no responde, el servicio no
  arranca: la configuración no se inventa.
- Sin Consul (tests y desarrollo local), todo sale del entorno, como antes.
- Lo implementan `app/core/consul_config.py` (lee el KV) y `cargar_settings()` en
  `app/core/config.py`.

## Arquitectura

El proyecto utiliza la arquitectura de capas definida para
`microservicios-pdf`:

```text
app/
├── main.py
├── controllers/
│   └── validation_controller.py
├── schemas/
│   └── validation_request.py
├── services/
│   └── validation_service.py
├── models/
│   └── pdf_validation_result.py
└── core/
    ├── composition.py
    ├── config.py
    └── exceptions.py
tests/
├── unit/
│   └── test_validation_service.py
└── integration/
    ├── conftest.py
    └── test_validation_http.py
```

Dirección de dependencias:

```text
controller → service
```

Este microservicio no persiste información ni llama a otros servicios, así que
no tiene repositorio ni adaptadores en `core/`: el contrato lo excluye
explícitamente (no usa MongoDB ni Redis). Agregar un puerto sin implementación
real sería código muerto.

El servicio se arma en `app/core/composition.py` (único lugar donde se lee la
configuración) y el controller lo recibe con `Depends`. El tamaño máximo llega
al servicio por constructor, sin valor por defecto.

Reglas respetadas:

- El controller maneja HTTP y no contiene reglas de negocio.
- El service no importa FastAPI.
- Los schemas Pydantic están separados de los modelos de dominio.
- Los modelos de dominio son Python puro.
- No se importa MongoDB, Motor ni Redis.

## Instalación con uv

Requiere Python 3.10 o superior y
[uv](https://docs.astral.sh/uv/).

Desde la raíz de este microservicio:

```bash
uv sync
```

## Ejecución local

```bash
uv run uvicorn app.main:app --reload
```

Las dependencias directas y las herramientas de desarrollo están fijadas a
versiones exactas en `pyproject.toml`; `uv.lock` fija además todas sus
dependencias transitivas.

El servicio queda disponible en `http://localhost:8000`.

## Ejemplos de uso

### Healthcheck

```bash
curl -i http://localhost:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok"
}
```

### Validación exitosa

El campo `archivo_base64` debe contener el Base64 real de un PDF, no los
caracteres literales `JVBERi0xLjQK...`.

```bash
curl -X POST http://localhost:8000/validar \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: prueba-validacion-001" \
  -d '{
    "archivo_base64": "<BASE64_DEL_PDF>",
    "nombre": "contrato.pdf"
  }'
```

### Generar Base64 desde un archivo

En PowerShell:

```powershell
$base64 = [Convert]::ToBase64String(
  [IO.File]::ReadAllBytes(".\contrato.pdf")
)

$body = @{
  archivo_base64 = $base64
  nombre = "contrato.pdf"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/validar `
  -ContentType "application/json" `
  -Body $body
```

## Tests y calidad

`uv sync` instala también el grupo `dev` (pytest, httpx, ruff, black). La
imagen Docker usa `uv sync --no-dev` y no los incluye.

La suite es hermética: no necesita MongoDB, Redis, red, otros microservicios
ni `.env`. Los tests de integración inyectan el servicio con un límite fijo
(`app.dependency_overrides`), así que un `.env` local con otro
`PDF_MAX_SIZE_MB` no cambia el resultado.

```bash
uv run pytest -v
uv run ruff check app tests
uv run black --check app tests
```

Los tests cubren:

- Tests unitarios directos del servicio:
  - PDF válido.
  - Base64 inválido.
  - contenido vacío.
  - contenido que no es PDF.
  - PDF corrupto.
  - PDF demasiado grande.
  - catálogo escrito sin espacio (`/Type/Catalog`) o dentro de un object stream.
  - Base64 con saltos de línea.
- Tests de integración HTTP:
  - healthcheck.
  - `POST /validar`.
  - status HTTP y formato de respuesta de cada código de error del contrato.
  - `nombre` o `archivo_base64` faltantes o en blanco → `VALIDATION_ERROR`.
  - error no previsto → `INTERNAL_ERROR` (con un servicio de prueba inyectado).
  - propagación de `X-Correlation-ID`.
  - logs con `correlation_id`, evento de PDF aceptado, sin datos sensibles,
    inicio y apagado en el `lifespan`.
- Tests unitarios de logs: `LOG_LEVEL` inválido y formato de `logging.json`.

Queda fuera de los tests automatizados, a propósito: la imagen Docker (se
verifica con el healthcheck al levantarla) y el apagado con `SIGTERM`, que depende
del proceso de uvicorn y se probó a mano (ver "Finalización segura").

## Docker

```bash
docker build -t validacion-pdf:1.2.0 .
docker run --rm -p 8000:8000 --env-file .env validacion-pdf:1.2.0
```

La versión del servicio es la de `pyproject.toml` (1.2.0): es la que muestra Swagger en
`/docs` y el tag de la imagen. `tests/integration/test_openapi.py` verifica que
`FastAPI(version=...)` en `app/main.py` coincida con `pyproject.toml`; en una versión
nueva se cambian los dos.

La imagen corre con el usuario sin privilegios `appuser` y tiene un
`HEALTHCHECK` contra `/health`.

## Estado del microservicio

La implementación actual incluye el contrato HTTP, la validación de negocio,
todos los errores del contrato, el healthcheck, la trazabilidad con logs y los
tests unitarios y de integración.

## Deuda técnica declarada

- **TDD en la primera entrega.** Los commits iniciales trajeron el código y
  los tests juntos, sin un commit rojo previo. Desde los arreglos de la
  auditoría (rama `fix/auditoria-validacion-pdf`), cada cambio de
  comportamiento sigue el ciclo test rojo → implementación → refactor.
- **Tamaño medido después de decodificar.** El límite se controla sobre los
  bytes ya decodificados, así que un request enorme se decodifica entero antes
  de rechazarse. El tamaño del body se puede limitar antes, en Traefik.
- **Validación estructural acotada.** Se verifica `%PDF`, `%%EOF` y que el
  documento no requiera contraseña usando PyMuPDF. La validación profunda la
  hace `extraccion-texto`, que responde `PDF_CORRUPTED` si no puede leer el
  archivo o no tiene páginas.
- **PDF con contraseña.** Se detecta acá, en `ValidationService.validate`: PyMuPDF
  abre el documento y `needs_pass` dice si pide contraseña. Se responde
  `PDF_INVALID` con `details.reason = "protegido_con_contrasena"` y no un código
  propio, porque el contrato no lo define y el orquestador devuelve como `500`
  cualquier código que no conoce. Un PDF que solo tiene contraseña de dueño
  (restringe permisos como imprimir o copiar) se abre sin ella y se acepta.
- **Puerto fijo en la imagen (8000).** Docker Compose y Traefik lo mapean; no
  hace falta una variable porque el contrato no la define.

El microservicio queda preparado para ser utilizado por el orquestador y
publicado como repositorio independiente en GitHub.
