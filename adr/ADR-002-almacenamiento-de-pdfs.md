# ADR-002: PDFs del aspirante en disco, fuera de lo que se sirve, con nombre UUID y validados por su contenido

**Estado:** Aceptado  
**Fecha:** 04/11/2026  
**Autor:** Francisco Buscaglia (rol: Desarrollador Backend)  
**Revisores:** Luca (PR F5), Enzo (revisión de arquitectura)

---

## Contexto

Cada aspirante sube entre 5 y 7 PDFs: DNI, títulos, partida de nacimiento, constancia de CUIT/CUIL y formularios firmados (US-CORE-003). Son documentos con datos personales, que el coordinador revisa y que hay que conservar al menos 5 años después de la graduación (BR-006). El SRS pide que solo se acepten PDFs de hasta 5 MB (RF-CORE-002) y que nadie pueda llegar a un documento ajeno (NFR-S02). Un archivo subido por un usuario no es confiable: su nombre, su extensión y el tipo que declara el navegador los elige quien lo sube.

---

## Opciones Evaluadas

### Opción A: Archivos en disco, en un volumen que no sirve ninguna URL, con su metadata en la base
**Descripción:** el archivo va a `{STORAGE_PATH}/uploads/{cohorte_id}/{legajo_id}/{uuid}.pdf` y la tabla `documentos` guarda la ruta relativa, el nombre original, el tamaño y el SHA-256. Solo se descarga por endpoints que controlan quién lo pide.  
**Ventajas:** simple, sin servicios nuevos; en Docker el volumen `pdfs` sobrevive a `docker compose down`; la base queda chica y los backups de la base y de los archivos se manejan por separado.  
**Desventajas:** la base y el disco pueden desincronizarse (una fila sin archivo o un archivo sin fila) si algo falla en el medio; para varios servidores haría falta un disco compartido.

### Opción B: Archivos dentro de la base (columna `bytea`)
**Descripción:** el contenido del PDF va en la misma fila de `documentos`.  
**Ventajas:** una sola transacción: nunca se desincronizan; un único backup.  
**Desventajas:** la base crece de a 5 MB por archivo (unos 35 MB por aspirante en el peor caso), los backups y las consultas se vuelven pesadas, y cada descarga carga el archivo entero en memoria.

### Opción C: Almacenamiento de objetos (S3, MinIO)
**Descripción:** los archivos van a un bucket privado y se descargan con URLs firmadas que vencen.  
**Ventajas:** escala sin límite y lo ofrece cualquier nube.  
**Desventajas:** suma un servicio más al `docker-compose`, credenciales y otra librería, para el volumen de una sola facultad. Con URLs firmadas, el control de quién descarga pasa a depender del vencimiento de la URL.

### Opción D: Carpeta pública servida como archivos estáticos
**Descripción:** guardar los PDFs en una carpeta que sirve el front o la API directamente.  
**Ventajas:** descargas sin código.  
**Desventajas:** cualquiera con la URL baja el documento, sin control de acceso. Descartada por NFR-S02.

---

## Decisión

"Decidimos usar **la opción A: los PDFs en disco, en un volumen que no sirve ninguna URL, con nombre UUID, su SHA-256 en la base y validados por sus primeros bytes**, porque cubre la seguridad que pide el SRS sin sumar servicios y deja la base liviana."

### Cómo queda

- **Validación** (`domain/pdf.py`): el archivo tiene que empezar con `%PDF-` (los "magic bytes" del formato) y pesar como mucho 5 MB. La extensión y el Content-Type no se miran. Si no cumple, 422 `ARCHIVO_INVALIDO` con los mensajes del SRS: "Solo se aceptan archivos en formato PDF" y "El archivo es demasiado grande. Máximo permitido: 5MB".
- **Tipo y estado:** solo se aceptan los tipos que le corresponden a ese legajo (`documentos_requeridos`: los 5 obligatorios, más el título de posgrado o el formulario de beca si aplican) y solo en BORRADOR u OBSERVADO; si no, 422 en `tipo` o 409 `LEGAJO_NO_EDITABLE`.
- **En disco** (`infrastructure/almacenamiento.py`): `{STORAGE_PATH}/uploads/{cohorte_id}/{legajo_id}/{uuid}.pdf`. En Docker, `STORAGE_PATH` es `/var/postgrado-storage`, montado en el volumen `pdfs`.
- **En la base** (`documentos`): ruta relativa, nombre original, tamaño, SHA-256 y fecha de subida. Como mucho uno por tipo y legajo: subir otro lo reemplaza.
- **Descargas:** `GET /seguimiento/{token}/documentos/{id}/download` (el aspirante, solo de su legajo) y `GET /documentos/{id}/download` (el coordinador). Responden `application/pdf` con `Content-Disposition: inline`, `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`.

### Decisiones de implementación

1. **El nombre en disco es un UUID nuevo, nunca el que eligió el aspirante.** Así un nombre como `../../main.py` no puede escribir fuera de la carpeta, dos archivos no chocan y el nombre no revela nada. El nombre original se guarda solo para mostrarlo y para el nombre de la descarga, sin la ruta que mandan algunos navegadores (`C:\fakepath\dni.pdf` queda `dni.pdf`) y con 255 caracteres como máximo.
2. **Se lee como mucho 5 MB + 1 byte.** Alcanza para saber que el archivo se pasa, sin cargar en memoria uno enorme.
3. **Orden de escritura para que base y disco no se desincronicen:** primero se escribe el archivo nuevo, después la fila. Si la base falla, se borra el archivo recién escrito. Al reemplazar, el archivo viejo se borra recién cuando la base ya cambió: si la base fallaba, la fila seguía apuntándole.
4. **Un documento ajeno da el mismo 404 que uno que no existe.** Así no se puede averiguar qué ids existen probando links.
5. **`ruta_del_pdf` nunca sale de `STORAGE_PATH`.** Las rutas las arma el back, pero si la base tuviera una ruta rara (por ejemplo, con `../`), la descarga la frena en vez de leer cualquier archivo del servidor.
6. **SHA-256 de cada archivo.** Permite comprobar más adelante que el archivo no cambió en disco y detectar duplicados; hoy se devuelve en la respuesta de la subida.

---

## Consecuencias

### Positivas
- Nadie llega a un PDF sin pasar por un endpoint que controla quién es.
- Un archivo que no es PDF (un ejecutable renombrado, una imagen) no se guarda nunca.
- La base guarda solo metadata: los backups son livianos.
- En Docker, los PDFs sobreviven a reiniciar los contenedores.

### Negativas (trade-offs aceptados)
- Base y disco son dos lugares: hay que respaldar los dos (el volumen `pdfs` y la base).
- Si alguien borra un archivo a mano, su fila queda y la descarga da 404.
- Con varios servidores haría falta un disco compartido o pasar a la opción C.
- `%PDF-` al principio prueba que el archivo dice ser PDF, no que sea un PDF sano: un PDF malicioso igual pasa. Lo mitiga que se descarga con `nosniff` y lo abre el visor del navegador.

### Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|-----------|
| Subir un archivo que no es PDF con extensión `.pdf` | Validación por magic bytes, no por extensión ni Content-Type |
| Escribir fuera de la carpeta con un nombre manipulado | Nombre UUID en disco; `ruta_del_pdf` no sale de `STORAGE_PATH` |
| Ver el documento de otro aspirante | El aspirante solo descarga de su legajo (404 igual para ajeno o inexistente); el coordinador necesita su rol |
| Archivos enormes que llenen la memoria o el disco | Se leen como mucho 5 MB + 1 byte; la base además tiene `tamanio_bytes` entre 1 byte y 5 MB |
| El navegador o un proxy guarda una copia del PDF | `Cache-Control: no-store` |
| Fila y archivo desincronizados | Orden de escritura de la decisión 3 |
| Dos subidas del mismo tipo al mismo tiempo | La base garantiza una fila por tipo; la segunda daría 500 (anotado como `shortcut` en el repositorio) |

---

## Revisión

Esta decisión será revisada en: la entrega final v1.0.  
Criterio de revisión: si el sistema pasa a correr en más de un servidor, o si el volumen de archivos crece mucho, conviene evaluar la opción C (almacenamiento de objetos) manteniendo las descargas detrás de los endpoints actuales.
