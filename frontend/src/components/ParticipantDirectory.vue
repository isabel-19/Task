<script setup>
  import { ref, computed, watch } from 'vue';
  import { api, can } from '../api';
  import { human } from '../modules';
  const props = defineProps({ modelValue: Boolean });
  const emit = defineEmits(['update:modelValue', 'assign']);
  const people = ref([]),
    search = ref(''),
    loading = ref(false),
    error = ref(''),
    imported = ref(0);
  const key = (value) =>
    String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  const filtered = computed(() =>
    people.value.filter((p) => key([p.name, ...p.aliases].join(' ')).includes(key(search.value))),
  );
  async function load() {
    loading.value = true;
    error.value = '';
    try {
      const data = await api('/participants');
      people.value = data.items;
      imported.value = data.imported_count;
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }
  watch(
    () => props.modelValue,
    (open) => {
      if (open) {
        search.value = '';
        load();
      }
    },
    { immediate: true },
  );
  function assign(person) {
    emit('update:modelValue', false);
    emit('assign', person.id);
  }
</script>
<template>
  <q-dialog :model-value="modelValue" @update:model-value="(v) => emit('update:modelValue', v)">
    <q-card class="record-detail participant-directory">
      <q-card-section class="row items-center"
        ><div>
          <span class="eyebrow">PERSONAS Y ASIGNACIONES</span>
          <h2>Participantes del equipo</h2>
          <p>{{ imported }} nombres registrados desde el Excel</p>
        </div>
        <q-space /><q-btn flat round icon="close" aria-label="Cerrar participantes" v-close-popup
      /></q-card-section>
      <q-separator />
      <q-card-section>
        <q-input
          v-model="search"
          outlined
          clearable
          label="Buscar participante"
          @clear="search = ''"
          ><template #prepend><q-icon name="search" /></template
        ></q-input>
        <p class="info-note q-mt-md">
          Cada nombre se conserva como aparece en el libro. Las diferencias de escritura que podrían
          referirse a una misma persona se señalan para revisión.
        </p>
        <q-linear-progress v-if="loading" indeterminate />
        <q-banner v-if="error" class="error-banner" role="alert"
          >{{ error }}<template #action><q-btn flat label="Reintentar" @click="load" /></template
        ></q-banner>
        <div v-for="person in filtered" :key="person.id" class="participant-row">
          <div>
            <b>{{ person.name }}</b
            ><small
              >{{ person.roles.map(human).join(', ') }} · {{ person.source }} ·
              {{ person.task_count }} tareas visibles</small
            >
            <small v-if="person.local_access && person.identifier"
              >Acceso local: {{ person.identifier }}</small
            >
            <small v-if="person.possible_variants.length" class="identity-note"
              >Revisar posible variante con {{ person.possible_variants.join(', ') }}.</small
            >
          </div>
          <q-btn
            v-if="can('tasks.write')"
            outline
            no-caps
            color="primary"
            label="Asignar tarea"
            icon="add_task"
            @click="assign(person)"
          />
        </div>
        <p v-if="!loading && !filtered.length" class="related-empty">
          No hay participantes con ese nombre.
        </p>
        <p class="info-note q-mt-lg">
          Los identificadores locales no son correos institucionales. Las contraseñas están en el
          archivo de accesos de esta instalación.
        </p>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>
