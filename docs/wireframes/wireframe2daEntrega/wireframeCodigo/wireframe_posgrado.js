/* ═══════════════════════════════════════════════════════════
   SISTEMA DE POSGRADO · UTN FRLP — Wireframe JS
   ═══════════════════════════════════════════════════════════ */


/* ─────────────────────────────────────────────────────────
   Navegación entre pantallas
   ──────────────────────────────────────────────────────── */

/**
 * Muestra la pantalla con el id dado y marca el nav-item como activo.
 * @param {string} screenId  - sufijo del id del screen (ej: 'dashboard')
 * @param {HTMLElement} navEl - el .nav-item que disparó el click
 */
function showScreen(screenId, navEl) {
  // Ocultar todas las pantallas
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));

  // Desactivar todos los nav-items
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Activar la pantalla y el nav-item correspondientes
  const target = document.getElementById('s-' + screenId);
  if (target) target.classList.add('active');
  if (navEl) navEl.classList.add('active');
}


/* ─────────────────────────────────────────────────────────
   Toggle de período de inscripción
   ──────────────────────────────────────────────────────── */

/**
 * Alterna el estado del toggle de período abierto/cerrado.
 * Actualiza el color del toggle y el texto de estado.
 * @param {HTMLElement} toggleEl - el .toggle-sw que disparó el click
 */
function togglePeriodo(toggleEl) {
  const isClosed = toggleEl.classList.toggle('closed');
  const statusEl = toggleEl.nextElementSibling;

  if (statusEl) {
    statusEl.textContent = isClosed ? 'Cerrado' : 'Abierto';
    statusEl.style.color = isClosed ? 'var(--red-text)' : '#22c55e';
  }

  // Actualizar también el indicador del sidebar footer
  const dotEl = document.querySelector('.dot-green');
  const footerText = document.querySelector('.sidebar-footer-text');
  if (dotEl)       dotEl.style.background  = isClosed ? 'var(--red-text)' : '#22c55e';
  if (footerText)  footerText.lastChild.textContent = isClosed ? ' Período cerrado' : ' Período abierto';
}


/* ─────────────────────────────────────────────────────────
   Celdas de asistencia (toggle P / A / vacío)
   ──────────────────────────────────────────────────────── */

/**
 * Alterna la celda de asistencia entre: vacío → P → A → vacío.
 * Recalcula el porcentaje de asistencia de la fila.
 * @param {HTMLElement} cell - la .att-cell clickeada
 */
function toggleAsistencia(cell) {
  const states = ['att-blank', 'att-p', 'att-a'];
  const labels = ['', 'P', 'A'];

  // Detectar estado actual
  let currentIdx = states.findIndex(cls => cell.classList.contains(cls));
  if (currentIdx === -1) currentIdx = 0;

  // Ir al siguiente estado
  const nextIdx = (currentIdx + 1) % states.length;

  // Aplicar nuevo estado
  states.forEach(cls => cell.classList.remove(cls));
  cell.classList.add(states[nextIdx]);
  cell.textContent = labels[nextIdx];

  // Recalcular asistencia de la fila
  recalcularAsistenciaFila(cell);
}

/**
 * Recalcula el porcentaje de asistencia en la fila de la celda.
 * Actualiza la barra de progreso y el texto porcentual.
 * @param {HTMLElement} cell - cualquier .att-cell de la fila
 */
function recalcularAsistenciaFila(cell) {
  const row = cell.closest('tr');
  if (!row) return;

  const cells = row.querySelectorAll('.att-cell');
  const total = cells.length;
  if (total === 0) return;

  const presentes = [...cells].filter(c => c.classList.contains('att-p')).length;
  const pct = Math.round((presentes / total) * 100);

  // Actualizar barra de progreso si existe en la fila
  const bar = row.querySelector('.progress-fill');
  const pctText = row.querySelector('.pct-text');

  if (bar) {
    bar.style.width = pct + '%';
    bar.className = 'progress-fill ' + (pct >= 75 ? 'pf-green' : pct >= 50 ? 'pf-yellow' : 'pf-red');
  }
  if (pctText) {
    pctText.textContent = pct + '%';
    pctText.style.color = pct < 50 ? 'var(--red-text)' : '';
  }
}


/* ─────────────────────────────────────────────────────────
   Opciones de beca
   ──────────────────────────────────────────────────────── */

/**
 * Marca/desmarca una opción de beca.
 * Solo permite una seleccionada a la vez.
 * @param {HTMLElement} optEl - el .beca-opt clickeado
 */
function toggleBeca(optEl) {
  const sibling = optEl.parentElement.querySelectorAll('.beca-opt');
  sibling.forEach(el => el.classList.remove('selected'));
  optEl.classList.toggle('selected');
}

/**
 TEMA OSCURO
 */
function toggleTheme() {
  document.body.classList.toggle('dark-theme');

  localStorage.setItem(
    'theme',
    document.body.classList.contains('dark-theme')
      ? 'dark'
      : 'light'
  );
}

/* Restaurar tema guardado */
document.addEventListener('DOMContentLoaded', () => {
  const theme = localStorage.getItem('theme');

  if (theme === 'dark') {
    document.body.classList.add('dark-theme');
  }
});