## TP 2 — Escáner de documentos

**Materia:** Procesamiento Digital de Imágenes  
**Proyecto:** Transformación de fotografías en documentos escaneados  
**Integrantes:** Fernanda Fava e Ignacio (completar nombre y apellido antes de entregar)  
**Repositorio:** https://github.com/ioanne/tps-proc-img  
**Rama de trabajo:** `Lab03_01_tp2_FTB`

## 1. Objetivo

Desarrollar un escáner de documentos que, a partir de una fotografía, identifique los bordes del documento, detecte sus cuatro esquinas, corrija su perspectiva y aplique filtros de imagen para producir un escaneo en PNG. El proyecto ofrece una interfaz web, una API REST y una interfaz de línea de comandos (CLI).

La consigna original de la cátedra se encuentra en [`enunciado.html`](enunciado.html).

## 2. Funcionalidades

- Detección automática de un documento cuadrilateral mediante procesamiento de imágenes.
- Identificación y ordenamiento de las esquinas en el orden superior izquierda, superior derecha, inferior derecha e inferior izquierda.
- Corrección geométrica de perspectiva y recorte del documento.
- Modos de salida: color, escala de grises y blanco y negro.
- Corrección de color y suavizado configurable de colores intensos.
- Guardado del resultado PNG, la fotografía original y los metadatos JSON.
- Consulta, listado y eliminación de escaneos desde la API.
- Procesamiento desde una interfaz web y desde la terminal.
- Manejo de errores, como imágenes inválidas, formatos no admitidos y ausencia de documento detectable.

## 3. Tecnologías

- **Python 3** para la lógica del procesamiento.
- **OpenCV y NumPy** para detección de bordes, contornos y transformación de perspectiva.
- **Pillow** para apertura de imágenes, orientación EXIF y codificación PNG.
- **FastAPI, Uvicorn y Pydantic** para la API, el servidor web y la validación de datos.
- **Pytest** para pruebas automatizadas.
- **HTML/CSS/JavaScript** para la interfaz web suministrada con el proyecto.

Las versiones admitidas están definidas en [`backend/requirements.txt`](backend/requirements.txt).

## 4. Arquitectura

El proyecto separa el procesamiento de imágenes de los mecanismos de entrada y salida:

```text
tp-2/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI, rutas y frontend
│   │   ├── config.py               # Configuración y almacenamiento
│   │   ├── repository.py           # Persistencia de escaneos
│   │   ├── schemas.py              # Modelos de datos
│   │   └── routers/
│   │       ├── detect.py           # Detección por API
│   │       └── scan.py             # Procesamiento y gestión por API
│   ├── docscan/
│   │   ├── __main__.py             # CLI
│   │   ├── detect.py               # Detección de documentos
│   │   ├── perspective.py          # Corrección geométrica
│   │   ├── scanner.py              # Coordinación detección + perspectiva
│   │   ├── filters.py              # Filtros polimórficos
│   │   ├── imageio.py              # Lectura y escritura de imágenes
│   │   └── exceptions.py           # Excepciones del dominio
│   ├── tests/                      # Pruebas automatizadas
│   └── requirements.txt
├── frontend/                       # Aplicación web
├── enunciado.html                  # Consigna
└── README.md
```

### Clases principales

- **`DocumentScanner`**: coordina la detección de esquinas con `detect_document` y la rectificación geométrica mediante `PerspectiveCorrector`.
- **`PerspectiveCorrector`**: calcula las dimensiones de salida, obtiene una matriz de transformación proyectiva y utiliza `cv2.warpPerspective`.
- **`Filter`**: clase abstracta con el método `apply(image)`; sus implementaciones incluyen `Color`, `GrayscaleFilter`, `BWFilter`, `ColorCorrectionFilter` y `SoftenColorsFilter`.
- **`ScanRepository`**: administra la persistencia de archivos PNG, originales y metadatos JSON en el directorio de almacenamiento.
- **`ScanOut` y `ScanOptions`**: contratos de respuesta y opciones de procesamiento definidos con Pydantic.

El **núcleo** `docscan` contiene la detección, la transformación y los filtros. Actualmente la API y la CLI componen la aplicación de filtros, mientras `DocumentScanner` coordina la detección y perspectiva; esto es una decisión de implementación que puede mejorarse centralizando la secuencia de filtros.

## 5. Flujo de procesamiento

1. Se recibe una fotografía por la interfaz web, API o CLI.
2. Se lee la imagen y se aplica su orientación EXIF si existe.
3. Se reduce una copia para localizar el documento de manera eficiente.
4. Se convierte a grises, se aplica desenfoque gaussiano y se extraen bordes con Canny.
5. Se realiza un cierre morfológico y se buscan contornos externos.
6. Se selecciona un contorno cuadrilateral convexo de tamaño suficiente y se ordenan sus cuatro esquinas.
7. Las coordenadas se trasladan al tamaño original; se calcula una transformación proyectiva para enderezar y recortar el documento.
8. Se aplican las opciones seleccionadas: corrección de color, suavizado y modo color/grayscale/B&W.
9. Se produce un PNG; en la API también se guardan original y metadatos.

**Nota:** el detector puede fallar cuando no encuentra un contorno cuadrilateral suficientemente definido. En ese caso se informa `DOCUMENT_NOT_FOUND`.

## 6. Instalación y ejecución

Desde la carpeta `tp-2`, abrir una terminal.

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8765
```

Si el entorno virtual ya existe, no es necesario volver a crearlo ni reinstalar dependencias.

### Linux / macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8765
```

Una vez iniciado el servidor:

- **Interfaz web:** http://127.0.0.1:8765/
- **Documentación interactiva:** http://127.0.0.1:8765/docs
- **Estado del servicio:** http://127.0.0.1:8765/api/health

La terminal del servidor debe permanecer abierta durante las pruebas.

## 7. Uso desde la interfaz web

1. Seleccionar una fotografía con las cuatro esquinas del documento visibles.
2. Elegir el modo **Color**, **Grayscale** o **B&W**.
3. Activar o desactivar la corrección de color y ajustar el suavizado según corresponda.
4. Ejecutar el escaneo y comparar la fotografía original con el resultado.
5. Consultar los escaneos previos en el panel lateral.

**Formatos admitidos en la API:** BMP, JPEG, PNG y WEBP. **Tamaño máximo:** 10 MB por imagen. El formato se valida por el contenido del archivo y no solamente por su extensión. MPO no está admitido.

## 8. Uso desde la terminal (CLI)

Desde `backend`:

```powershell
python -m docscan "C:\ruta\foto.jpg" "C:\ruta\escaneo.png" --color-mode grayscale
```

Otros ejemplos:

```powershell
python -m docscan foto.jpg escaneo.png --color-mode color
python -m docscan foto.jpg escaneo.png --color-mode bw --no-color-correction
python -m docscan foto.jpg escaneo.png --color-mode grayscale --soften-colors 0.5
```

El factor `--soften-colors` debe estar entre `0` y `1`. El archivo de salida se guarda como PNG.

## 9. API REST

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/api/health` | Comprobar el estado del servidor |
| `POST` | `/api/detect` | Detectar las cuatro esquinas de una foto |
| `POST` | `/api/scans` | Procesar una foto y guardar el escaneo |
| `GET` | `/api/scans` | Listar escaneos, del más reciente al más antiguo |
| `GET` | `/api/scans/{scan_id}` | Recuperar metadatos de un escaneo |
| `DELETE` | `/api/scans/{scan_id}` | Borrar el escaneo y sus archivos |

Los resultados se publican bajo `/media/`. La carpeta física se configura mediante la variable de entorno `TP_STORAGE_DIR`; si no se define, se utiliza `backend/storage`.

## 10. Pruebas automatizadas

Desde `backend`:

```powershell
python -m pytest -q
```

**Resultado obtenido en el entorno de desarrollo:** `93 passed in 7.05s`.

- **79 pruebas de aceptación** de la cátedra (`tests/test_contract.py`).
- **14 pruebas unitarias adicionales**, distribuidas en:
  - `test_core_unit.py` (3): perspectiva, preservación de colores y geometría degenerada.
  - `test_repository_unit.py` (5): guardado, recuperación, listado, eliminación e identificadores inválidos.
  - `test_detection_filters_unit.py` (6): detección, ausencia de documento y modos de filtrado.

**Importante para la entrega:** el resultado de 93 pruebas corresponde a una ejecución local posterior a la integración del PR #8. Los tres archivos de tests propios y un ajuste en `SoftenColorsFilter` deben incorporarse a GitHub antes de considerar el repositorio remoto actualizado con ese resultado.

## 11. Pruebas manuales con fotografías reales

Se verificó el funcionamiento en la interfaz web con los siguientes casos:

| Caso | Modo | Observación |
|---|---|---|
| Mouse pad rectangular sobre escritorio claro | Color | Detectó el contorno y produjo un recorte con perspectiva corregida |
| Mismo objeto | Grayscale | Convirtió la imagen a escala de grises y mantuvo el recorte |
| Mismo objeto | B&W | Binarizó la imagen; aparecieron puntos por la textura oscura del material |
| Hoja impresa de estudio sobre fondo contrastante | B&W | El título se mantuvo legible; se observó ruido en texto pequeño |
| Misma hoja impresa | Grayscale | Mejor conservación de texto y tonos; persistió una franja de fondo en el borde inferior |
| Fotografía MPO | Carga web | Formato rechazado con mensaje explicativo; no se procesó |

La hoja utilizada contenía el título **«Procesamiento Digital de Imágenes»**. En la prueba el detector identificó las esquinas superiores de forma razonable, pero situó la esquina inferior izquierda fuera del papel, por lo que el recorte incluyó parte de la mesa.

**Evidencias visuales:** antes de la entrega, incorporar capturas o fotografías al repositorio, por ejemplo en `evidencias/`, y enlazarlas aquí. No se incluyen imágenes en este README porque todavía no se han agregado esos archivos al repositorio.

## 12. Limitaciones conocidas y posibles mejoras

- **Contornos y contraste:** la detección depende de que el documento tenga bordes identificables y superficie suficiente en la fotografía.
- **Recortes imperfectos:** los fondos texturados o bordes poco definidos pueden desplazar una esquina; se observó una franja de escritorio en un caso real.
- **Papel curvado:** la transformación proyectiva endereza un plano, pero no elimina curvaturas físicas ni ondulaciones.
- **Binarización:** el filtro B&W puede resaltar ruido o pequeñas manchas, especialmente en superficies texturadas y sombras.
- **Escalado del procesamiento:** los filtros se encadenan en la API y la CLI; como mejora de diseño puede centralizarse esa secuencia en el núcleo reutilizable.
- **Formatos:** MPO no está admitido por la API.

No se implementaron OCR, corrección de curvatura avanzada ni edición manual de esquinas.

## 13. Trabajo colaborativo

Se utilizó Git y GitHub con una rama compartida para el TP (`Lab03_01_tp2_FTB`). El desarrollo combinó el detector y los filtros iniciales con la implementación de la corrección de perspectiva, la integración del escáner, la persistencia y la CLI. Estos aportes se integraron mediante el [Pull Request #8](https://github.com/ioanne/tps-proc-img/pull/8).

## Diagrama UML

El diseño de clases, las relaciones de herencia y las
dependencias principales del escáner están documentados
en el [diagrama UML del proyecto](docs/uml.md).

## Evidencias de pruebas reales

Se realizaron pruebas con una hoja con texto y un mouse pad, utilizando los modos Color, Grayscale y B&W.

Los resultados y las limitaciones observadas se encuentran en [Evidencias de pruebas reales](docs/evidencias/README.md).
