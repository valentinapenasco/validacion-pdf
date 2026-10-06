# validacion-pdf

Microservicio FastAPI del proyecto `microservicios-pdf` responsable de validar
archivos PDF recibidos en Base64. Está alineado con el contrato compartido
`microservicios-pdf v1.0.0`.

## Responsabilidad

El servicio recibe el contenido de un archivo PDF codificado en Base64 y
determina si puede continuar hacia los siguientes microservicios del flujo.

Hace:

- Recibir `archivo_base64` y `nombre`.
- Decodificar el contenido Base64.
- Validar que el contenido no esté vacío.
- Validar la firma `%PDF`.
- Validar una estructura mínima del PDF.
- Validar el tamaño máximo configurado.
- Informar el tamaño recibido en bytes.
- Propagar `X-Correlation-ID`.
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
| `POST` | `/api/v1/validar` | Alias versionado del endpoint de validación. |
| `GET` | `/health` | Healthcheck del servicio. |
| `GET` | `/api/v1/health` | Alias versionado del healthcheck. |

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

`archivo_base64` es obligatorio. `nombre` es opcional; si no se informa, se
utiliza `documento.pdf`.

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

Los errores producidos por las reglas de negocio utilizan el formato común:

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
| `PDF_INVALID` | `422` | Base64 inválido, contenido vacío o archivo que no es PDF. |
| `PDF_TOO_LARGE` | `413` | El tamaño supera `PDF_MAX_SIZE_MB`. |
| `PDF_CORRUPTED` | `422` | El contenido comienza como PDF, pero no tiene la estructura mínima esperada. |
| `VALIDATION_ERROR` | `400` | El request no cumple el schema de entrada. |
| `INTERNAL_ERROR` | `500` | Error interno no previsto. |

## Correlation ID

El servicio propaga la cabecera `X-Correlation-ID`:

- Si la petición trae la cabecera, conserva el valor recibido.
- Si no la trae, genera un identificador UUID.
- El identificador se devuelve en la cabecera de la respuesta.
- En las respuestas de error también aparece como `error.correlation_id`.

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
| `APP_VERSION` | `1.0.0` | Versión expuesta por FastAPI. |

El archivo `.env` no debe versionarse.

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
    ├── config.py
    ├── exceptions.py
    ├── repository.py
    └── database.py
tests/
├── unit/
│   └── test_validation_service.py
└── integration/
    └── test_validation_http.py
```

Dirección de dependencias:

```text
controller → service → repository → infraestructura
```

En este microservicio no se persiste información. El repositorio abstracto y
el adaptador en memoria existen para cumplir la arquitectura común y facilitar
las pruebas sin una base de datos.

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

## Tests

La suite es hermética: no necesita MongoDB, Redis, red ni otros
microservicios.

```bash
uv run pytest -v
```

Los tests cubren:

- Tests unitarios directos del servicio:
  - PDF válido.
  - Base64 inválido.
  - contenido vacío.
  - contenido que no es PDF.
  - PDF corrupto.
  - PDF demasiado grande.
  - nombre por defecto.
- Tests de integración HTTP:
  - healthcheck.
  - `POST /validar`.
  - `POST /api/v1/validar`.
  - status HTTP y formato de respuesta.
  - propagación de `X-Correlation-ID`.

## Estado del microservicio

La implementación actual incluye el contrato HTTP, la validación de negocio,
los errores principales, el healthcheck, la trazabilidad y los tests iniciales.

El microservicio queda preparado para ser utilizado por el orquestador y
publicado como repositorio independiente en GitHub.
