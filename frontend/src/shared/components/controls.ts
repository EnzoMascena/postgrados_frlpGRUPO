/* controls.ts — Estilo compartido de inputs, selects y textareas.
   En vez de repetir esta lista larga de clases en cada campo del
   formulario, la guardamos una vez acá y la importamos donde haga
   falta: si hay que cambiar el estilo de los campos, se toca solo
   este archivo. */
export const controlClass =
  'w-full px-3 py-2 rounded-input border border-line-strong bg-surface text-ink text-[13px] ' +
  'placeholder:text-faint focus:outline-none focus:border-primary transition-colors'