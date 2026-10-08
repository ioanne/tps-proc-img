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

La API base fue provista con los endpoints, el modelo ORM, las consultas a la base de datos,
el manejo de archivos y el servicio principal.
En este trabajo se completó el procesamiento de imágenes del core, incluyendo las diez
operaciones requeridas, las validaciones de parámetros y los tests unitarios propios.
Todos los test pasaron correctamente

## Integrantes

-Abigail Nina
-Gastón Ramirez
-Pablo Speranza
-Rocío Vázquez

## Descripción

La aplicación permite subir imágenes y aplicar distintas operaciones de procesamiento utilizando Pillow y OpenCV.

El frontend y la estructura general de la API fueron provistos como código base. En este trabajo se implementó el procesamiento de imágenes del core, 
incluyendo las diez operaciones requeridas y sus validaciones.

Las operaciones disponibles son:

- Brillo
- Contraste
- Saturación
- Nitidez
- Escala de grises
- Desenfoque
- Detección de bordes
- Rotación
- Espejo
- Redimensionamiento

## Tests propios

Además de los tests de aceptación provistos por la cátedra, se agregaron tests unitarios propios para verificar el comportamiento del core.

Se incluyeron tests para:

- las diez operaciones de procesamiento;
- las validaciones de parámetros inválidos;
- el funcionamiento de `ImageCodec.open`;
- el funcionamiento de `ImageCodec.encode`.

Los tests propios se encuentran en:

- `tests/test_operations.py`
- `tests/test_codec.py`

Para ejecutarlos:

```bash
pytest tests/test_operations.py -v
pytest tests/test_codec.py -v
```

## Diagrama de clases

El núcleo de procesamiento se organiza alrededor de una clase abstracta `Operation` de la cual heredan las diez operaciones implementadas.

`ImageService` coordina el flujo general de la aplicación y utiliza `ImageCodec` para abrir y codificar imágenes, además de `FileStorage` e `ImageDAL` para el manejo de archivos y persistencia.

```mermaid
classDiagram

    class ImageService {
        -ImageDAL dal
        -FileStorage storage
        -ImageCodec codec
        +upload()
        +list()
        +get()
        +delete()
        +apply()
    }

    class ImageCodec {
        +inspect(content)
        +open(content)
        +encode(image, format)
    }

    class Operation {
        <<abstract>>
        +name
        +parameters
        +apply(image)
    }

    class Brightness
    class Contrast
    class Saturation
    class Sharpness
    class Grayscale
    class Blur
    class Edges
    class Rotation
    class Mirror
    class Resize

    Operation <|-- Brightness
    Operation <|-- Contrast
    Operation <|-- Saturation
    Operation <|-- Sharpness
    Operation <|-- Grayscale
    Operation <|-- Blur
    Operation <|-- Edges
    Operation <|-- Rotation
    Operation <|-- Mirror
    Operation <|-- Resize

    ImageService --> ImageCodec
    ImageService --> Operation
    ImageService --> FileStorage
    ImageService --> ImageDAL


## Uso de Pillow y OpenCV

Se utilizaron Pillow y OpenCV de forma complementaria, según el tipo de operación.

Pillow se utilizó principalmente para operaciones directas sobre color y transformaciones simples:

- brillo con `ImageEnhance.Brightness`;
- contraste con `ImageEnhance.Contrast`;
- saturación con `ImageEnhance.Color`;
- nitidez con `ImageEnhance.Sharpness`;
- escala de grises con `ImageOps.grayscale`;
- espejo con `ImageOps`;
- rotación con `Image.rotate`.

OpenCV se utilizó principalmente para operaciones de filtrado y procesamiento:

- desenfoque gaussiano con `cv2.GaussianBlur`;
- desenfoque de mediana con `cv2.medianBlur`;
- desenfoque promedio con `cv2.blur`;
- detección de bordes con `cv2.Canny`;
- redimensionamiento con `cv2.resize`.    

## Conversión entre Pillow y OpenCV

Pillow y OpenCV utilizan distinto orden para los canales de color.

Pillow trabaja normalmente con imágenes en formato `RGB`, mientras que OpenCV utiliza `BGR`.

Por este motivo, la conversión entre ambas representaciones se centralizó en funciones auxiliares reutilizables dentro del core evitando repetir la misma lógica en cada operación.

También se contempla el modo `RGBA`, preservando correctamente el canal alfa cuando corresponde.

Este enfoque permite utilizar OpenCV para algunas operaciones y luego volver a una imagen de Pillow antes de que el resultado sea codificado y almacenado.