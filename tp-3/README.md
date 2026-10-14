# TP 3 — Avatar retro (presencial)

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

## Línea de comandos

```bash
cd backend
python -m retro foto.jpg avatar.png --palette pico8 --pixels 64 --dithering --steps pasos/
```

## Tests

Un archivo por paso, para ir de a uno:

```bash
cd backend
pytest tests/test_step1_square_crop.py -v
pytest tests/test_step2_shrink.py -v
pytest tests/test_step3_enlarge.py -v
pytest tests/test_step4_palette.py -v
pytest tests/test_step5_frame.py -v
pytest tests/test_step6_dithering.py -v
pytest                                   # todo, incluida la API
```

Viene todo hecho (frontend, API, pipeline, paletas, tests y el paso `GradientMap` como ejemplo) salvo los seis
pasos de `backend/retro/steps.py`, que hoy lanzan `StepNotImplemented`. Mientras falten, el pipeline los saltea y el
frontend igual funciona. En el estado inicial los tests dan `94 failed, 21 passed`; el trabajo es lograr que pasen
todos.

## Imágenes de prueba

Las de `frontend/samples/` son de dominio público, vía Wikimedia Commons:

- `vermeer.jpg`: Johannes Vermeer, *La joven de la perla* (c. 1665).
- `einstein.jpg`: Albert Einstein, foto de Orren Jack Turner (1947, copyright no renovado).

## Integrantes
Lauger Natera
Matias Rodriguez
