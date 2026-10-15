<script setup>
  import { ref } from 'vue';
  import { useRouter, useRoute } from 'vue-router';
  import { login } from '../api';
  import RouteMotif from '../components/RouteMotif.vue';
  const router = useRouter(),
    route = useRoute();
  const email = ref(''),
    password = ref(''),
    busy = ref(false),
    error = ref(''),
    visible = ref(false);
  async function submit() {
    busy.value = true;
    error.value = '';
    try {
      await login(email.value, password.value);
      const next = String(route.query.next || '/');
      await router.replace(
        next.startsWith('/') && !next.startsWith('//') && !next.startsWith('/login') ? next : '/',
      );
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
</script>
<template>
  <main class="login-page">
    <section class="login-story">
      <div class="brand-light">
        <q-icon name="account_balance" size="34px" />
        <div><b>UNAJMA</b><small>Oficina de Gestión de la Calidad</small></div>
      </div>
      <div class="login-heading">
        <span class="eyebrow light">ROADMAP OGC</span>
        <h1>Una ruta compartida.<br />Una gestión conectada.</h1>
        <p>
          Planes, personas y evidencias en un mismo lugar. Cada compromiso, un paso hacia la mejora.
        </p>
        <div class="login-flow">
          <span>Planificar</span><q-icon name="east" /><span>Verificar</span
          ><q-icon name="east" /><span>Mejorar</span>
        </div>
        <RouteMotif />
      </div>
      <span class="login-footer">Universidad Nacional José María Arguedas</span>
    </section>
    <section class="login-form">
      <div class="login-form-inner">
        <span class="eyebrow">BIENVENIDO A TU ESPACIO DE TRABAJO</span>
        <h2>Iniciar sesión</h2>
        <p class="muted">Accede con tu cuenta asignada por la OGC.</p>
        <q-form @submit="submit" class="q-gutter-y-lg q-mt-xl"
          ><q-input
            v-model="email"
            outlined
            label="Correo o identificador de acceso"
            type="email"
            autocomplete="username"
            :rules="[(v) => !!v || 'Ingresa tu identificador']" /><q-input
            v-model="password"
            outlined
            label="Contraseña"
            :type="visible ? 'text' : 'password'"
            autocomplete="current-password"
            :rules="[(v) => !!v || 'Ingresa tu contraseña']"
            ><template #append
              ><q-btn
                flat
                round
                :icon="visible ? 'visibility_off' : 'visibility'"
                aria-label="Mostrar u ocultar contraseña"
                @click="visible = !visible" /></template></q-input
          ><q-banner v-if="error" class="error-banner" role="alert">{{ error }}</q-banner
          ><q-btn
            type="submit"
            color="primary"
            no-caps
            unelevated
            label="Entrar al espacio de trabajo"
            class="full-width login-submit"
            :loading="busy"
        /></q-form>
        <div class="login-note">
          <q-icon name="info_outline" /><span
            >Tu cuenta es administrada por la OGC. Si necesitas acceso o ayuda con tu contraseña,
            comunícate con la persona responsable de la oficina.</span
          >
        </div>
      </div>
    </section>
  </main>
</template>
