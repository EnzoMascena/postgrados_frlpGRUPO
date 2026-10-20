"""
Módulo auth — login del coordinador y del CPR, y "¿quién soy?".

Es el EJEMPLO para copiar: tiene los mismos archivos que cada módulo del
sistema, y leerlos en este orden es recorrer un request de punta a punta.

    controller.py   → la ruta HTTP: recibe, delega y elige el status code
    dependencies.py → el cableado: get_session → repository → service
    service.py      → el caso de uso: las reglas, sin saber de HTTP
    repository.py   → las consultas a la base, sin reglas
    schemas.py      → el contrato: lo que entra y sale, en camelCase

(Los módulos con lógica de negocio suman un reglas.py con funciones puras;
auth no lo necesita: sus reglas son las de core/security.py.)
"""
