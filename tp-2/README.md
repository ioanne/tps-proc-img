# TP 2 — Escáner de documentos

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
python -m docscan foto.jpg escaneo.png --color-mode grayscale --soften-colors 0.5
```

## Tests de aceptación

```bash
cd backend
pytest tests/test_contract.py -v
```

Se entregan el frontend, los tests, los schemas (`app/schemas.py`) y los routers
(`app/routers/`) con los endpoints declarados, que por ahora responden ejemplos vacíos. También
viene resuelto todo lo de abrir imágenes y validar: `docscan/imageio.py` (abre la foto con EXIF,
convierte Pillow ↔ OpenCV, codifica el PNG), `docscan/exceptions.py`, `app/uploads.py` (validación
del archivo subido) y `app/errors.py` (traducción de excepciones a HTTP). Falta la detección del
documento, la corrección de perspectiva, los filtros, la CLI, el almacenamiento y completar cada
endpoint. En el estado inicial los tests dan `48 failed, 31 passed`; el trabajo del equipo es lograr
que pasen todos.

## Integrantes

## Integrantes
```bash
Abel Pablo Vincenti
Leonel Juiz
```

## Decisiones de diseño

- **Para empezar:**  Detección y perspectiva, diseñar el diagrama del core y revisar lo que ya viene implementado. Después, completar el core y probarlo con la CLI; seguir con /api/detect, almacenamiento y /api/scans; finalmente agregar los filtros y probar con fotos reales.
- **Una regla importante**: los filtros deben compartir una interfaz y aplicarse polimórficamente, para poder agregar uno nuevo sin sumar if/elif al bucle que los ejecuta. También hay que mantener docscan independiente de la API, usar excepciones de dominio y no modificar el frontend ni los archivos de tests indicados como protegidos.


# TP 2 — Escáner de Documentos (Backend & Core)

**Integrantes:**
- Abel Pablo Vincenti
- Leonel Juiz

---

## 📋 Resumen del Proyecto

Este proyecto consiste en el desarrollo completo del backend para un escáner digital de documentos. A partir de una fotografía tomada desde cualquier dispositivo (respetando orientación EXIF, iluminación y rotación), el sistema detecta automáticamente el documento, realiza la corrección de perspectiva para enderezarlo y recortarlo, y le aplica un pipeline de mejoras de imagen y modos de color.

El proyecto se divide estrictamente en dos capas aisladas:
1. **Core (`docscan`)**: Un paquete de Python desacoplado de la web que procesa imágenes con OpenCV/NumPy, expone una CLI y lanza excepciones de dominio.
2. **API REST (`app`)**: Una interfaz construida con FastAPI que expone los endpoints requeridos, valida los archivos y gestiona la persistencia de escaneos y metadatos en disco.

---

## 🛠️ Arquitectura y Decisiones de Diseño

### 1. Núcleo Procesador de Imágenes (`docscan`)

- **Independencia absoluta:** `docscan` no importa ni depende de FastAPI, Starlette ni de ningún módulo de `app/`. Trabaja exclusivamente con matrices NumPy (BGR) y bytes.
- **Detector (`docscan/detector.py`)**: 
  - Procesa una copia reducida de la imagen para garantizar velocidad.
  - Combina detección de bordes (Canny) y umbralización adaptativa (Otsu) con operaciones morfológicas (`MORPH_CLOSE`) para cerrar contornos.
  - Identifica el contorno convexo de 4 vértices con mayor área (mínimo 15% del área total).
  - Reordena las esquinas en sentido horario: *Top-Left*, *Top-Right*, *Bottom-Right*, *Bottom-Left*.
  - En caso de no hallar un cuadrilátero válido, lanza la excepción de dominio `DocumentNotFound` con un mensaje explicativo en español.
- **Corrección de Perspectiva (`docscan/warper.py`)**:
  - Calcula las dimensiones máximas (ancho y alto) a partir de la distancia euclidiana de las esquinas.
  - Proyecta y rectifica la imagen con `cv2.getPerspectiveTransform` y `cv2.warpPerspective`, conservando la resolución y relación de aspecto original del documento.
- **Filtros Polimórficos (`docscan/filters.py`)**:
  - Se diseñó una interfaz abstracta `Filter` con el método `apply(image) -> image`.
  - Se implementaron las clases concretas:
    - `ColorCorrectionFilter`: Balance de blancos por canal estirando percentiles altos para remover dominantes amarillas.
    - `SoftenColorsFilter`: Convierte a espacio HSV y suaviza colores saturados mediante el ajuste gradual de saturación y brillo según el parámetro `soften_colors`.
    - `GrayscaleFilter`: Conversión a 1 solo canal (grises).
    - `BWFilter`: Umbralización adaptativa (`cv2.adaptiveThreshold`) para obtener fondo blanco puro y texto/tinta negra.
  - El escáner ejecuta la secuencia de filtros polimórficamente sin condicionales `if/elif` en el bucle principal.
- **Orquestador (`docscan/scanner.py`)**: Coordina el pipeline completo: `Detector` $\rightarrow$ `PerspectiveWarper` $\rightarrow$ `FilterChain`.
- **Línea de Comandos (`docscan/__main__.py`)**: Permite ejecutar el core directamente desde la terminal (`python -m docscan entrada.jpg salida.png ...`).

---

### 2. Capa API y Almacenamiento (`app`)

- **Repositorio de Almacenamiento (`app/repository.py`)**:
  - Se creó la clase `ScanRepository` que encapsula la persistencia en `config.STORAGE_DIR`.
  - Cada escaneo genera un identificador único (UUID v4) y guarda tres archivos:
    1. `<id>.png`: El escaneo final procesado.
    2. `<id>-original.<ext>`: La fotografía original recibida byte por byte.
    3. `<id>.json`: Metadatos completos del contrato `ScanOut`.
  - Valida sanitización de IDs contra *path traversal* lanzando `ScanNotFound` (404) si el ID no existe o no cumple el patrón regex.
- **Endpoints (`app/routers/`)**:
  - `POST /api/detect`: Llama al detector del core y retorna las coordenadas reescaladas de las 4 esquinas.
  - `POST /api/scans`: Procesa la foto con las opciones de filtro elegidas y persiste el resultado (HTTP 201).
  - `GET /api/scans`: Devuelve la lista de escaneos ordenados del más reciente al más antiguo.
  - `GET /api/scans/{id}`: Retorna el escaneo y sus metadatos.
  - `DELETE /api/scans/{id}`: Elimina los tres archivos asociados de disco (HTTP 204).
- **Manejo de Errores (`app/errors.py`)**:
  - Mapeo automático de excepciones de dominio (`ScanError`, `DocumentNotFound`, `InvalidImage`) a respuestas JSON normalizadas con código HTTP (400, 422, 404).

---

## 🚀 Cómo Ejecutarlo

### Levantar la API
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8765