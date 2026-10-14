# Diagrama UML — TP 2: Escáner de documentos

Este diagrama representa las clases principales implementadas en el núcleo de procesamiento (`docscan`) y en la capa de API y persistencia (`app`). Se omiten funciones auxiliares para facilitar la lectura.

```mermaid
classDiagram
    direction TB

    class DocumentScanner {
        +corrector: PerspectiveCorrector
        +scan(image: ndarray) tuple
    }

    class PerspectiveCorrector {
        +correct(image: ndarray, corners: ndarray) ndarray
    }

    class Filter {
        <<abstract>>
        +apply(image: ndarray) ndarray*
    }

    class Color {
        +apply(image: ndarray) ndarray
    }
    class GrayscaleFilter {
        +apply(image: ndarray) ndarray
    }
    class BWFilter {
        +apply(image: ndarray) ndarray
    }
    class ColorCorrectionFilter {
        +apply(image: ndarray) ndarray
    }
    class SoftenColorsFilter {
        +factor: float
        +apply(image: ndarray) ndarray
    }

    class Photo {
        +format: str
        +image: ndarray
        +width: int
        +height: int
    }

    class ScanRepository {
        +storage_dir: Path
        +save(scan: ScanOut, image_png: bytes, original_content: bytes) ScanOut
        +get(scan_id: str) ScanOut
        +list() list~ScanOut~
        +delete(scan_id: str) None
    }

    class ScanOptions {
        +color_mode: ColorMode
        +color_correction: bool
        +soften_colors: float
    }

    class ScanOut {
        +id: str
        +original_name: str
        +url: str
        +original_url: str
        +width: int
        +height: int
        +size_bytes: int
        +corners: list
        +options: ScanOptions
        +created_at: datetime
    }

    class ScanError {
        <<exception>>
    }
    class InvalidImage {
        <<exception>>
    }
    class DocumentNotFound {
        <<exception>>
    }

    DocumentScanner *-- PerspectiveCorrector : contiene
    DocumentScanner ..> Photo : procesa imagen de
    DocumentScanner ..> DocumentNotFound : puede propagar

    Filter <|-- Color
    Filter <|-- GrayscaleFilter
    Filter <|-- BWFilter
    Filter <|-- ColorCorrectionFilter
    Filter <|-- SoftenColorsFilter
    BWFilter ..> GrayscaleFilter : utiliza

    ScanOut *-- ScanOptions : opciones
    ScanRepository ..> ScanOut : persiste

    ScanError <|-- InvalidImage
    ScanError <|-- DocumentNotFound
```

## Flujo de procesamiento

1. `read_photo` interpreta la imagen de entrada y aplica la orientación EXIF cuando corresponde.
2. `detect_document` localiza un cuadrilátero y devuelve las cuatro esquinas en orden.
3. `DocumentScanner` usa `PerspectiveCorrector` para rectificar la región detectada.
4. La API o la CLI aplica los filtros elegidos: corrección de color, suavizado y modo final (`Color`, `GrayscaleFilter` o `BWFilter`).
5. `encode_png` convierte la imagen procesada a PNG. En la API, `ScanRepository` guarda el PNG, el original y los metadatos JSON.

**Alcance del diagrama:** `detect_document`, `read_photo` y `encode_png` son funciones, no clases. Los filtros se aplican actualmente desde la API y la CLI, y no desde `DocumentScanner`. Se representan las dependencias principales, no todas las llamadas internas.
