export default defineContentScript({
  matches: ['*://*.u-cursos.cl/*'],
  main() {
    console.log('Hello content.');
  },
});
