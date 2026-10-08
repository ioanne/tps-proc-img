# TP 1 - Procesamiento de Imágenes

## ¿De qué trata?

Este trabajo consiste en implementar diferentes operaciones de procesamiento de imágenes utilizando Python, Pillow y OpenCV.

La idea fue completar la lógica del procesamiento en el backend, respetando la estructura que ya tenía el proyecto y manteniendo separada la lógica de imágenes de la API.

## ¿Qué hicimos?

Completamos las operaciones principales de procesamiento de imágenes:

- Brillo
- Contraste
- Saturación
- Nitidez
- Escala de grises
- Desenfoque
- Detección de bordes
- Rotación
- Espejado
- Redimensionado

También completamos la conversión entre imágenes de Pillow y OpenCV para poder utilizar ambas librerías según la operación.

Además, agregamos validaciones para los parámetros que pueden generar errores.

## Pruebas

Se realizaron pruebas unitarias y pruebas de validación para comprobar que las operaciones funcionen correctamente.

## ¿Qué partes del código modificamos?

### `app/core/imaging.py`

Se agregaron las funciones necesarias para convertir imágenes entre Pillow y OpenCV.

#### `pil_to_cv2()`

Convierte una imagen de Pillow a un array de OpenCV.

Se tiene en cuenta la conversión de imágenes RGB y RGBA para mantener correctamente los canales.

#### `cv2_to_pil()`

Realiza la conversión inversa, pasando un array de OpenCV nuevamente a una imagen de Pillow.

También contempla los modos RGB y RGBA.

Estas funciones permiten utilizar Pillow y OpenCV dentro de las diferentes operaciones sin repetir la lógica de conversión.

---

### `app/core/operations.py`

En este archivo se implementaron las operaciones de procesamiento.

#### `Operation`

Es la clase abstracta base de todas las operaciones.

Define la estructura común y el método:

```python
apply(image)
```

Cada operación concreta implementa este método.

#### `EnhanceOperation`

Es una clase base utilizada para las operaciones que utilizan `ImageEnhance` de Pillow.

A partir de ella se implementaron:

- `Brightness`
- `Contrast`
- `Saturation`
- `Sharpness`

Cada una recibe un factor y aplica la mejora correspondiente sobre la imagen.

#### `Brightness`

Utiliza `ImageEnhance.Brightness` para modificar el brillo.

#### `Contrast`

Utiliza `ImageEnhance.Contrast` para modificar el contraste.

#### `Saturation`

Utiliza `ImageEnhance.Color` para modificar la saturación.

#### `Sharpness`

Utiliza `ImageEnhance.Sharpness` para modificar la nitidez.

#### `Grayscale.apply()`

Convierte la imagen a escala de grises.

Se utiliza OpenCV para realizar la conversión y el resultado se devuelve en modo `L`.

#### `Blur.apply()`

Implementa los diferentes tipos de desenfoque:

- Gaussian
- Median
- Average

Para estas operaciones se utiliza OpenCV.

También se valida que el tamaño del kernel sea impar.

#### `Edges.apply()`

Realiza la detección de bordes mediante `cv2.Canny()`.

Recibe:

- `lower_threshold`
- `upper_threshold`

y valida que el umbral inferior sea menor que el superior.

El resultado se devuelve en escala de grises.

#### `Rotation.apply()`

Realiza la rotación de la imagen utilizando Pillow.

Se permite indicar el ángulo y si se debe expandir el resultado para conservar toda la imagen.

Cuando corresponde, se utiliza un fondo transparente o negro.

#### `Mirror.apply()`

Permite espejar la imagen horizontal o verticalmente.

Para esto se utilizan:

```python
ImageOps.mirror()
```

y

```python
ImageOps.flip()
```

#### `Resize.apply()`

Permite cambiar el tamaño de la imagen.

Si se mantiene la relación de aspecto, la altura se calcula automáticamente a partir del nuevo ancho.

También permite indicar ancho y alto de forma independiente cuando no se quiere mantener la relación de aspecto.

---

## Tests agregados

Se agregaron pruebas específicas para comprobar tanto el funcionamiento de las operaciones como sus validaciones.

### `tests/test_operations_unit.py`

Contiene pruebas para las diferentes operaciones de procesamiento.

### `tests/test_operations_validation.py`

Contiene pruebas para casos inválidos, por ejemplo:

- Kernel par en `Blur`
- Umbrales invertidos o iguales en `Edges`
- Falta de altura en `Resize` cuando no se mantiene la relación de aspecto

### `tests/test_codec.py`

Contiene pruebas relacionadas con la apertura y codificación de imágenes y con las conversiones RGB y RGBA.

## Integrantes

- Eric Silvestri
- Lucas Suarez
- Walter Willich

