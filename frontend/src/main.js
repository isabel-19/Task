import { createApp } from 'vue';
import { Quasar, Notify, Dialog } from 'quasar';
import lang from 'quasar/lang/es';
import '@quasar/extras/material-icons/material-icons.css';
import '@quasar/extras/roboto-font/roboto-font.css';
import 'quasar/dist/quasar.css';
import './style.css';
import App from './App.vue';
import { router } from './router';

createApp(App)
  .use(Quasar, {
    plugins: { Notify, Dialog },
    lang,
    config: {
      brand: {
        primary: '#157f75',
        secondary: '#223c43',
        accent: '#d69945',
        positive: '#157f75',
        negative: '#c25952',
        warning: '#bd8638',
      },
    },
  })
  .use(router)
  .mount('#app');
