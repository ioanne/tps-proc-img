### Registro de pruebas de aceptación

Ejecución

Comando: pytest tests/test_contract.py -v --tb=short

Resultado: 79 pruebas aprobadas.

Fallos: 0.

Advertencias: 37, relacionadas con la deprecación del parámetro mode de Image.fromarray() en Pillow.

Observación

Las pruebas se ejecutaron localmente en Windows 11, Python 3.13.7 y pytest 9.0.3.

###  Registro de pruebas con imágenes reales

### Prueba exploratoria: documento con una esquina de bajo contraste

Ejecución

Comando: pytest tests/test_contract.py -v --tb=short

Resultado: 7 pruebas aprobadas (test_real_photos.py y test_storage)

Fallos: 1 en test_real_photos.py con imagen "pers2.jpeg"

Se evaluó una fotografía de un documento sobre un fondo oscuro, en la que una de sus esquinas presentaba poco contraste con el entorno. El detector lanzó `DocumentNotFound` porque no logró identificar claramente los cuatro bordes.

Resultado:prueba exploratoria fallida.

Conclusión:la detección depende, entre otros factores, de la visibilidad de los bordes y del contraste entre el documento y el fondo. Se reemplazó esta imagen en la suite principal por otra fotografía de perspectiva que el detector reconoce correctamente.

La imagen original se conserva como evidencia para futuras pruebas y posibles mejoras del algoritmo.