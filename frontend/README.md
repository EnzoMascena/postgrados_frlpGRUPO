# Frontend — Sistema de Posgrado UTN FRLP

Interfaz web del sistema de gestión de posgrado. Digitaliza el ciclo completo:
preinscripción del aspirante, cursada, seguimiento y graduación.

## Stack

| Tecnología | Uso |
|---|---|
| React 19 | Librería de UI |
| TypeScript | Tipado estático |
| Vite | Build y servidor de desarrollo |
| TailwindCSS v4 | Estilos mediante clases utilitarias |
| TanStack Query | Fetching y caché de datos (se activa en la Entrega 3) |
| Tabler Icons | Iconografía |

## Cómo levantarlo

Requiere Node.js 20 o superior.

```bash
cd frontend
npm install
npm run dev
```

Abre en http://localhost:3000

Otros comandos:

```bash
npm run build     # build de producción
npm run lint      # linter
```

## Estructura

Sigue **Screaming Architecture**: las carpetas nombran la funcionalidad, no la
tecnología. Cada feature es autónoma y contiene sus propias páginas,
componentes y datos.

```
src/
├── auth/                   Inicio de sesión
├── inscripcion/            Preinscripción del aspirante
├── planilla-docente/       Carga de asistencia y notas
├── estadisticas/           Indicadores y reportes
├── shared/                 Transversal a todas las features
│   ├── layout/             Sidebar, Topbar
│   └── components/         Card, Button, Badge, Field, StatCard...
├── App.tsx                 Layout raíz y navegación entre pantallas
└── index.css               Design tokens (bloque @theme de Tailwind)
```

Cada feature se organiza igual:

```
feature/
├── pages/          Pantalla completa
├── components/     Piezas propias de esa pantalla
├── data/           Datos mockeados (temporal)
└── types.ts        Tipos del dominio
```

## Estado de las pantallas

| Pantalla | Rol | Estado |
|---|---|---|
| Login | Todos | Completa |
| Inscripción | Aspirante | Completa |
| Planilla docente | Docente | Completa |
| Estadísticas | Conducción | Completa |
| Legajo | Conducción | Pendiente |
| Dashboard | Conducción | Pendiente |

## Diseño

Los tokens de diseño están centralizados en el bloque `@theme` de
`src/index.css`. Definirlos ahí genera las utilidades de Tailwind
automáticamente: `--color-primary` habilita `bg-primary`, `text-primary`,
`border-primary`.

Principales:

```
--color-primary   #2C5F8A   Azul institucional UTN
--color-sidebar   #1E293B   Fondo del menú lateral
--color-ok        #16A34A   Estado favorable
--color-warn      #D97706   Estado de alerta
--color-danger    #DC2626   Estado crítico
```

El modo oscuro redefine los mismos tokens bajo la clase `.dark`, por lo que
toda la interfaz se adapta sin duplicar estilos.

> **No usar otra librería de CSS** (Bootstrap, Material UI). Convivirían con
> Tailwind pisándose los resets y los colores, y romperían el modo oscuro.

## Datos

Las pantallas consumen datos mockeados desde el archivo `data/` de cada
feature. La forma de esos datos ya replica la respuesta esperada de la API,
por lo que en la Entrega 3 solo cambia el origen: el mock se reemplaza por una
consulta con TanStack Query, sin tocar los componentes.

## Convenciones

Antes de contribuir, leer `CONTRIBUTING.md` en la raíz del repositorio.

- Ramas: `feature/US-[MOD]-[NNN]-[descripcion-corta]`
- Commits: Conventional Commits — `feat(alcance): descripción en presente`
- Todo cambio entra por Pull Request