# Guía de uso · Sistema de Posgrado UTN FRLP

> **Versión v0.5 (Core).** Las capturas son de esta versión.

Para levantarlo: `docker compose up --build` y entrar a http://localhost:3000. Los emails de prueba llegan a MailHog: http://localhost:8025.

## Aspirante

El aspirante no tiene usuario ni contraseña: entra con el link que le llega por email.

### 1. Inscribirse

En http://localhost:3000/inscripcion completás tus datos, elegís una o dos carreras y, si querés, pedís beca; al tocar "Guardar y continuar con la documentación" se crea tu preinscripción.

![Formulario de preinscripción](guia/aspirante-01-formulario.jpg)

### 2. Recibir el link

Te llega un email con tu código de seguimiento y el botón "Continuar mi preinscripción", que vence a los 60 días.

![Email con el link de seguimiento](guia/aspirante-02-email-link.jpg)

### 3. Ver tu preinscripción

Con el link entrás a "Mi preinscripción", donde ves el estado, qué documentos te faltan y tus datos.

![Página de seguimiento](guia/aspirante-03-seguimiento.jpg)

### 4. Subir los PDFs

En cada documento tocás "Seleccionar archivo PDF": solo se aceptan PDF de hasta 5 MB, y si subís otro del mismo tipo reemplaza al anterior.

![Subida de documentos, con un error y dos cargados](guia/aspirante-04-subir-pdfs.jpg)

### 5. Enviar a revisión

Cuando tenés todos los documentos obligatorios, "Enviar a revisión" se habilita y te pide confirmar antes de mandar.

![Confirmación de envío](guia/aspirante-05-enviar.jpg)

Al confirmar, la página pasa a Pendiente, te avisa "Recibimos tu preinscripción" y te llega un email con tu código de seguimiento.

![Preinscripción enviada](guia/aspirante-05b-enviado.jpg)

### 6. Recuperar el link

Si perdiste el email, en la parte de arriba del formulario escribís tu email y tocás "Enviarme el link".

![Recuperar el link](guia/aspirante-06-recuperar-link.png)

### 7. Ver una observación y corregir

Si la Secretaría te pide algo, lo ves arriba de todo en amarillo; corregís, tocás "Reenviar corrección" y confirmás.

![Legajo con observaciones](guia/aspirante-07-observado.png)

Si lo que hay que corregir es un dato, tocás "Editar mis datos", lo cambiás y guardás; si es un documento, subís el PDF nuevo en su lugar.

![Editar mis datos](guia/aspirante-07b-editar-datos.jpg)

Cuando terminaste, tocás "Reenviar corrección" y confirmás: vuelve a Pendiente y te llega el email "Recibimos tu corrección".

![Reenviar la corrección](guia/aspirante-07c-reenviar.jpg)

### 8. Ver la aprobación

Cuando te aprueban, ves tu número de legajo y la fecha límite para matricularte.

![Legajo aprobado](guia/aspirante-08-aprobado.jpg)

## Coordinador

### 1. Entrar

En http://localhost:3000/login entrás con tu email y contraseña (en desarrollo: `admin@fenix.test` / `Admin1234!`).

![Login](guia/coordinador-01-login.png)

### 2. Ver el dashboard

Arriba ves los totales de la cohorte y, abajo, todos los inscriptos con su estado y cuántos documentos subieron.

![Dashboard](guia/coordinador-02-dashboard.jpg)

### 3. Buscar y filtrar

Buscás por DNI (con o sin puntos) o por apellido (3 letras como mínimo) y combinás los filtros de estado, carrera y beca.

![Búsqueda por apellido](guia/coordinador-03-buscar.png)

### 4. Abrir y cerrar el período

Con el interruptor "Período de inscripción" de arriba a la derecha abrís o cerrás la inscripción de la cohorte; al cerrarla podés poner la fecha de la próxima apertura, que el formulario le muestra al aspirante.

![Cerrar la inscripción](guia/coordinador-04-periodo.jpg)

### 5. Abrir un legajo

En el dashboard tocás "Ver legajo" y ves los datos, las carreras y la beca, los documentos, el historial y las acciones que se pueden hacer en ese estado.

![Detalle del legajo](guia/coordinador-05-detalle.jpg)

### 6. Ver un PDF

En "Documentación" tocás "Ver" al lado del documento y el PDF se abre en una ventana, sin salir del legajo.

![Vista previa de un PDF](guia/coordinador-06-ver-pdf.jpg)

### 7. Pasar a revisión

En un legajo Pendiente tocás "Pasar a revisión": queda En revisión y el cambio se anota en el historial.

![Legajo pasado a revisión](guia/coordinador-07-revisar.jpg)

### 8. Observar

Si falta algo, tocás "Observar" y escribís qué tiene que corregir: al aspirante le llega por email y el legajo queda Observado ("Rechazar" funciona igual, con un comentario opcional).

![Observar el legajo](guia/coordinador-08-observar.jpg)

### 9. Aprobar

Tocás "Aprobar" y confirmás: se asigna el número de legajo y el aspirante recibe un email con 30 días para matricularse.

![Confirmar la aprobación](guia/coordinador-09-aprobar.jpg)

Al confirmar, el número de legajo aparece arriba y en el aviso, y el legajo queda Completado.

![Legajo aprobado](guia/coordinador-09b-aprobado.jpg)

### 10. Matricular

Cuando el aspirante se matricula, en el legajo Completado tocás "Matricular" y confirmás: pasa a Activo.

![Confirmar la matrícula](guia/coordinador-10-matricular.jpg)

### 11. Exportar a Excel

Con la búsqueda y los filtros que quieras, tocás "Exportar" y se baja `inscriptos-cohorte2026-AAAA-MM-DD.xlsx` con los mismos legajos de la tabla.

![Botón Exportar del dashboard](guia/coordinador-11-exportar.jpg)
