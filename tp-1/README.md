# TP 1 - Procesamiento de Imágenes


En este trabajo práctico trabajamos sobre un editor de imágenes y completamos la parte del backend encargada de realizar las distintas operaciones sobre las imágenes.

Para hacerlo usamos principalmente **Pillow** y **OpenCV**, siguiendo la estructura que ya tenía armado el proyecto.

El trabajo se centró principalmente en estos dos archivos:

- `app/core/imaging.py`
- `app/core/operations.py`

En `imaging.py` agregamos las funciones necesarias para convertir imágenes entre Pillow y OpenCV, ya que algunas operaciones se realizan más cómodamente utilizando una librería u otra.

En `operations.py` implementamos las 10 operaciones que pedía el TP:

- Brillo
- Contraste
- Saturación
- Nitidez
- Escala de grises
- Desenfoque
- Detección de bordes
- Rotación
- Espejado
- Redimensionamiento

También agregamos las validaciones necesarias para los parámetros de las operaciones. Por ejemplo, el tamaño del kernel utilizado en el desenfoque tiene que ser impar y, para la detección de bordes, el límite inferior tiene que ser menor que el superior.


*##  Pruebas*

Para comprobar que lo que hicimos funcionara correctamente, además de las pruebas que ya venían con el proyecto agregamos nuestras propias pruebas.

Los archivos que agregamos fueron:

```text
tests/test_operations_unit.py
tests/test_operations_validation.py
tests/test_codec.py

*## ¿Qué partes del código modificamos?*

### `app/core/imaging.py`

En este archivo agregamos las funciones:

```python
pil_to_cv2()
cv2_to_pil()

Las usamos para poder pasar una imagen de Pillow a OpenCV y volver a convertirla a Pillow cuando termina el procesamiento.

También se completaron las funciones del ImageCodec que se encargan de abrir y guardar las imágenes:
ImageCodec.open()
ImageCodec.encode()

open() recibe los bytes de una imagen y la prepara para que pueda ser procesada, normalizando los modos de color a L, RGB o RGBA.

encode() hace el proceso inverso: toma la imagen procesada y la convierte nuevamente en bytes para poder guardarla. También tiene en cuenta casos como guardar una imagen RGBA en formato JPEG, donde primero hay que convertirla a RGB.

##app/core/operations.py
En este archivo implementamos las operaciones que faltaban.
Primero dejamos la clase base:
Operation
y agregamos una clase auxiliar:
EnhanceOperation
Esta última nos permitió reutilizar la misma lógica para las operaciones que utilizan ImageEnhance de Pillow.

Brillo, contraste, saturación y nitidez
Se implementaron:
Brightness
Contrast
Saturation
Sharpness

Cada una utiliza la clase correspondiente de ImageEnhance:
ImageEnhance.Brightness
ImageEnhance.Contrast
ImageEnhance.Color
ImageEnhance.Sharpness

Todas reciben un factor y aplican el cambio sobre la imagen.

Escala de grises
Se implementó:
Grayscale.apply()

Para esta operación utilizamos OpenCV y convertimos la imagen a modo L.

Desenfoque
Se implementó:
Blur.apply()

Permite trabajar con tres métodos:
gaussian
median
average

Para realizar los filtros utilizamos las funciones correspondientes de OpenCV.
También agregamos una validación en el constructor de Blur para comprobar que el tamaño del kernel sea impar.


Detección de bordes
Se implementó:
Edges.apply()

Utilizando:
cv2.Canny()

Rotación
Se implementó:
Rotation.apply()

utilizando el método rotate() de Pillow.

Se tiene en cuenta el modo de la imagen para definir el color de relleno y, en el caso de RGBA, se utiliza transparencia.

Espejado
Se implementó:
Mirror.apply()

Para el espejado horizontal utilizamos:
ImageOps.mirror()

y para el vertical:
ImageOps.flip()


Redimensionamiento
Se implementó:
Resize.apply()

Permite indicar solamente el ancho cuando se quiere conservar la relación de aspecto, calculando automáticamente el alto.

También permite indicar ancho y alto cuando no se quiere conservar la proporción.

*## Tests que agregamos*
Para comprobar los cambios agregamos:
tests/test_operations_unit.py
tests/test_operations_validation.py
tests/test_codec.py

test_operations_unit.py prueba las 10 operaciones.
test_operations_validation.py prueba los casos en los que los parámetros no son válidos.
test_codec.py prueba ImageCodec y las conversiones entre Pillow y OpenCV.

*## Integrantes*

- Eric Silvestri
- Lucas Suarez
- Walter Willich
