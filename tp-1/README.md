# TP 1 — Editor de imágenes con Pillow y OpenCV

La consigna completa está en [`enunciado.html`](enunciado.html) (abrilo en el navegador).

## Cómo correrlo

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8765
```

- Frontend: http://localhost:8765
- Documentación de la API: http://localhost:8765/docs

## Tests de aceptación

```bash
cd backend
pytest tests/test_contract.py -v
```

La API ya está armada (endpoints, modelo ORM, consultas en `app/dal.py`, archivos en
`app/core/storage.py`, el servicio en `app/core/service.py` y la subida de imágenes con
`ImageCodec.inspect`). Falta el procesamiento de imágenes: `ImageCodec.open` y `ImageCodec.encode`
en `app/core/imaging.py` y las diez operaciones en `app/core/operations.py`, que hoy
responden **501 Not Implemented**. En el estado inicial los tests dan `121 failed, 32 passed`; el
trabajo del equipo es implementar esas clases y lograr que pasen todos.

## Integrantes

- _completar_
