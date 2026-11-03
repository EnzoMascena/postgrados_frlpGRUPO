# Guía de Contribución — postgrado Posgrado

Leé este documento antes de hacer tu primer commit. Estas convenciones existen para que el trabajo de 4 personas en paralelo no genere caos.

---

## 1. Estrategia de Ramas (GitFlow simplificado)

```
main          ← Solo versiones estables. Tags de release (v0.5, v1.0). NUNCA push directo.
  └── develop ← Integración continua. Aquí mergean los features. NUNCA push directo.
        └── feature/US-CORE-001-formulario-inscripcion  ← Tu rama de trabajo
        └── feature/US-B-002-planilla-asistencia
        └── fix/bug-descripcion-del-bug
        └── docs/actualizar-asr
```

**Regla de oro: Si no es un Pull Request, no existe.**

---

## 2. Nomenclatura de Ramas

```
feature/US-[MOD]-[NNN]-[descripcion-corta]
fix/[descripcion-del-bug]
docs/[descripcion]
refactor/[descripcion]
test/[descripcion]
```

**Ejemplos válidos:**
- `feature/US-CORE-001-formulario-inscripcion`
- `feature/US-B-002-planilla-asistencia`
- `fix/validacion-dni-duplicado`
- `docs/actualizar-swagger-legajos`

**Ejemplos inválidos:**
- `mi-rama` ← sin contexto
- `feature/arreglos` ← sin ID de historia
- `WIP` ← nunca mergear Work In Progress

---

## 3. Convención de Commits (Conventional Commits)

Formato: `tipo(alcance): descripción en presente, sin mayúscula inicial, sin punto final`

```
feat(core): agrega validación de DNI en formulario de inscripción
fix(auth): corrige expiración de JWT refresh token
docs(api): actualiza swagger para endpoint de documentos
test(semaforo): agrega tests para regla de semaforo rojo en Maestría
refactor(legajo): extrae lógica de transición de estados a clase LegajoStateMachine
chore(ci): configura pipeline de GitHub Actions para linting
```

**Tipos válidos:**

| Tipo | Cuándo usarlo |
|------|--------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `test` | Agrega o modifica tests |
| `refactor` | Refactorización sin cambio de comportamiento |
| `chore` | Tareas de mantenimiento (CI, dependencias) |
| `style` | Formato (linting, espacios) sin cambio de lógica |

**Referencia al requisito:** Si el commit implementa un requisito del SRS, incluirlo:
```
feat(core): implementa upload de PDFs con validación MIME

Implementa RF-CORE-002. El sistema verifica magic bytes del archivo
antes de almacenarlo, independientemente del Content-Type del cliente.
```

---

## 4. Pull Requests

### Cuándo abrir un PR
- Cuando la historia de usuario está **funcionando** (no cuando está "casi lista")
- Cuando los tests pasan localmente
- Cuando el linter no tiene errores

### Qué incluir en el PR

**Título:** Igual que el título de la historia de usuario. Ej: `[US-CORE-001] Formulario de inscripción de aspirantes`

**Descripción (template):**
```markdown
## ¿Qué hace este PR?
[Descripción de qué implementa en 2-3 oraciones]

## Historia de usuario
Closes #[número de issue en GitHub] — US-CORE-001

## Cambios principales
- [Lista de cambios relevantes]

## Cómo probarlo
1. Levantar el ambiente: `docker-compose up -d`
2. Ir a `http://localhost:3000/inscripcion`
3. Completar el formulario con datos válidos
4. Verificar que el legajo aparece en el dashboard del coordinador

## Screenshots (si hay cambios de UI)
[Imagen o GIF del antes/después]

## Checklist del DoD
- [ ] Tests pasando (cobertura ≥70% en lógica nueva)
- [ ] Linter sin errores
- [ ] Swagger actualizado (si hay endpoints nuevos)
- [ ] Probado en la máquina de otro integrante
- [ ] CHANGELOG.md actualizado
```

### Cómo vincular el PR con su issue

GitHub solo reconoce las palabras clave **en inglés** (`Closes`, `Fixes`, `Resolves`). Con «Cierra #23» el PR no queda vinculado al issue.

- **Si el PR completa la historia:** escribí `Closes #N — US-XXX-NNN`.
- **Si es solo una parte** (la historia se completa con otros PRs): escribí `Parte de #N — US-XXX-NNN`. Esa frase **no vincula** nada, así que enlazá el issue a mano desde **Development** (el panel de la derecha del PR).
- **El issue se cierra recién cuando el cambio llega a `main`**, que es la rama por defecto del repo: al mergear el PR a `develop` queda abierto, aunque esté vinculado. Para que se cierre, el PR de `develop` a `main` del release lista los `Closes #N` de las historias que incluye.

### Code Review: qué revisar

Como **reviewer**, enfocate en:
1. **¿La lógica de negocio es correcta?** (¿el semáforo calcula bien? ¿la transición de estados es válida?)
2. **¿Hay problemas de seguridad?** (¿se validan las entradas? ¿el endpoint tiene auth guard?)
3. **¿Los tests cubren los casos edge?** (null, strings vacíos, valores límite)
4. **¿El código es entendible?** (nombres claros, funciones cortas, comentarios donde hacen falta)

NO es responsabilidad del reviewer:
- Encontrar typos de UI (eso va en un issue separado)
- Revisar que el diseño "se vea lindo" (eso es del QA/UX)

---

## 5. Workflow Paso a Paso

```bash
# 1. Siempre trabajar desde develop actualizado
git checkout develop
git pull origin develop

# 2. Crear rama para la historia
git checkout -b feature/US-CORE-001-formulario-inscripcion

# 3. Desarrollar, commitear frecuentemente (no solo al final)
git add .
git commit -m "feat(core): agrega campos básicos del formulario de inscripción"
git commit -m "feat(core): agrega validación de DNI y email"
git commit -m "test(core): agrega tests de validación del formulario"

# 4. Antes de abrir el PR: sincronizar con develop
git fetch origin develop
git rebase origin/develop
# Si hay conflictos: resolverlos, luego git rebase --continue

# 5. Push y abrir PR en GitHub
git push origin feature/US-CORE-001-formulario-inscripcion
# Abrir PR en GitHub contra la rama develop

# 6. Después del merge: limpiar rama local
git checkout develop
git pull origin develop
git branch -d feature/US-CORE-001-formulario-inscripcion
```

---

## 6. Variables de Entorno

**NUNCA commitear el archivo `.env`**. Está en `.gitignore`.

Cuando agregues una variable nueva:
1. Agregala a `.env.example` con un valor de ejemplo (no real)
2. Documentala en el comentario del `.env.example`
3. Mencionala en la descripción del PR

```bash
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/postgrado_dev
JWT_SECRET=cambiar-en-produccion-por-secreto-seguro-32chars-min
SMTP_HOST=smtp.example.com
SMTP_PORT=587
STORAGE_PATH=/var/postgrado-storage  # Ruta donde se almacenan los PDFs
```

---

## 7. Comandos Útiles

```bash
# Levantar ambiente completo
docker-compose up -d

# Ver logs del backend en tiempo real
docker-compose logs -f backend

# Correr tests
npm test                  # o: pytest
npm run test:coverage     # con reporte de cobertura

# Linting
npm run lint              # o: flake8 src/
npm run lint:fix          # corrige automáticamente

# Migraciones de base de datos
npm run db:migrate        # aplica migraciones pendientes
npm run db:generate       # genera nueva migración desde cambio en schema

# Acceder a la base de datos
docker exec -it postgrado-db psql -U postgrado_user -d postgrado_dev
```

---

*¿Dudas sobre el proceso? → Canal `#postgrado-general` en Github Discussion o Issues en GitHub.*
