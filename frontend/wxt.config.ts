import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
    modules: ["@wxt-dev/module-react"],

    manifest: {
      name: "U-Filter",
      version: "1.0",
      permissions: ["storage"],
      host_permissions: ["https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/*", "*://*.u-cursos.cl/*"],
      content_scripts: [
      {
          matches: ["*://*.u-cursos.cl/*"],
          js: ["content-scripts/content.js"],
      },
    ],
    },
});
