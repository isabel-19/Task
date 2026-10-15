import { createApp } from 'vue';
import { Quasar, Notify, Dialog } from 'quasar';
import lang from 'quasar/lang/es';
import '@quasar/extras/material-icons/material-icons.css';
import '@quasar/extras/roboto-font/roboto-font.css';
import 'quasar/dist/quasar.css';
import './style.css';
import './theme.css';
import App from './App.vue';
import { router } from './router';

createApp(App)
  .use(Quasar, {
    plugins: { Notify, Dialog },
    lang,
    config: {
      brand: {
        primary: '#1d4ed8',
        secondary: '#12356b',
        accent: '#d69945',
        positive: '#15803d',
        negative: '#c25952',
        warning: '#bd8638',
        info: '#2563eb',
      },
    },
  })
  .use(router)
  .mount('#app');
