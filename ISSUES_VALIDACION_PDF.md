# Issues sugeridas para validacion-pdf

## 1) Crear la estructura base del microservicio con la arquitectura requerida
- Tipo: Epic
- Objetivo: preparar la estructura `app/`, `controllers/`, `schemas/`, `services/`, `models/`, `core/`, `main.py` y el packaging mínimo.
- Criterios de aceptación:
  - Existe `app/main.py` con FastAPI.
  - La estructura por capas sigue el contrato base del proyecto.
  - No incluye MongoDB ni Redis.

## 2) Definir el contrato HTTP de validación PDF
- Tipo: Story
- Objetivo: establecer la entrada/salida del endpoint `POST /validar` con Base64 y nombres de archivo.
- Criterios de aceptación:
  - Recibe `archivo_base64` y `nombre`.
  - Responde con `valido`, `nombre`, `tamano_bytes` en caso exitoso.
  - Responde con el formato de error común en errores de negocio.

## 3) Implementar la lógica de validación del PDF
- Tipo: Story
- Objetivo: decodificar Base64, validar que sea PDF y controlar tamaño máximo.
- Criterios de aceptación:
  - Rechaza Base64 inválido.
  - Rechaza archivos vacíos.
  - Rechaza archivos que no inician con `%PDF`.
  - Rechaza si supera `PDF_MAX_SIZE_MB`.

## 4) Agregar observabilidad y trazabilidad
- Tipo: Story
- Objetivo: exponer `GET /health` y propagar `X-Correlation-ID` en todas las respuestas.
- Criterios de aceptación:
  - `/health` responde `200` con estado saludable.
  - Si el cliente envía `X-Correlation-ID`, se devuelve en la respuesta.
  - Si no se envía, se genera uno automáticamente.

## 5) Crear tests de contrato y regresión
- Tipo: Task
- Objetivo: cubrir validaciones, errores y endpoint HTTP.
- Criterios de aceptación:
  - 4-5 tests cubren éxito y casos negativos.
  - Los tests se ejecutan con `pytest` sin base de datos.

## Título sugerido para el issue principal

- `feat(validacion-pdf): crear microservicio de validación de archivos PDF`
