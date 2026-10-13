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

<<<<<<< Updated upstream
La API, la persistencia, el almacenamiento y el procesamiento de imágenes están implementados.
Los tests de aceptación se ejecutan con el comando anterior.
=======
## Implementación del procesamiento de imágenes

Durante el desarrollo se investigó el flujo de la aplicación y sus distintas líneas de código.
Al levantar el servidor apareció una excepción; al seguir el recorrido de las rutas y los servicios,
se identificó que cada operación debía invocar un método de su clase correspondiente. Por eso se
implementaron los métodos de procesamiento en `app/core/operations.py` y se conectaron con el flujo
existente de la API. Este trabajo se realizó con apoyo de herramientas de IA.

Quedaron implementadas las diez operaciones para editar imágenes:

- Brillo y contraste.
- Saturación y nitidez.
- Escala de grises y desenfoque.
- Detección de bordes.
- Rotación y espejo.
- Cambio de tamaño.

Se probaron las operaciones con imágenes, incluyendo ajustes de contraste y rotación, para comprobar
el resultado visual. La implementación está disponible en la rama
[`Lab03_01-griselda`](https://github.com/ioanne/tps-proc-img/tree/Lab03_01-griselda/tp-1).
>>>>>>> Stashed changes

## Integrantes

- Blanco, Griselda
- Fava, Fernanda
- Toto, Ignacio
