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

La API, la persistencia, el almacenamiento y el procesamiento de imágenes están implementados.
Los tests de aceptación se ejecutan con el comando anterior.

## Integrantes

- Blanco, Griselda
- Fava, Fernanda
- Toto, Ignacio
