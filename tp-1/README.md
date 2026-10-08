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
```bash
Abel Pablo Vincenti
Leonel Juiz
```

## Decisiones de diseño

- **Polimorfismo (patrón Strategy):** cada operación hereda de `Operation` e implementa `apply`. El servicio recibe una operación y llama a ese método, sin necesitar un `if/elif` para elegir entre brillo, blur, rotación, etc. Algunas operaciones sí usan condiciones internas para elegir una variante, como el tipo de blur o la dirección del espejo.
- **Pillow:** se usa para brillo, contraste, saturación, nitidez, escala de grises, rotación y espejo. Son transformaciones que Pillow ofrece directamente y permiten trabajar con imágenes sin convertirlas manualmente a matrices.
- **OpenCV:** se usa para blur, detección de bordes y redimensionado, porque ofrece filtros y algoritmos de procesamiento adecuados para esas tareas.
- **NumPy:** convierte la imagen a una matriz de píxeles para pasarla a OpenCV; el resultado se vuelve a convertir a imagen de Pillow.
- **Validación:** las reglas específicas de cada operación se validan antes del procesamiento; si un parámetro no es válido, se informa con `InvalidParameters`.
