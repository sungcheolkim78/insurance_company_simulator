if (typeof globalThis.localStorage === 'undefined') {
  globalThis.localStorage = globalThis.jsdom.window.localStorage
}
