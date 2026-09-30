# validacion-pdf

Microservicio FastAPI para validar archivos PDF enviados en Base64.

## Contrato base

- Endpoint: `POST /validar`
- Alias: `POST /api/v1/validar`
- Health: `GET /health` y `GET /api/v1/health`
- Requiere `X-Correlation-ID` en cabeceras y lo devuelve en la respuesta
- No usa MongoDB ni Redis
- No extrae texto ni calcula checksum

## Variables de entorno

```bash
PDF_MAX_SIZE_MB=5
```

## Ejemplo de uso

```bash
curl -X POST http://localhost:8000/validar \
  -H "Content-Type: application/json" \
  -d '{
    "archivo_base64": "JVBERi0xLjQK...",
    "nombre": "contrato.pdf"
  }'
```
