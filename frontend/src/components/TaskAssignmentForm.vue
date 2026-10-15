<script setup>
  import { reactive, ref, computed, watch } from 'vue';
  import { api } from '../api';
  const props = defineProps({
    modelValue: Boolean,
    record: Object,
    preset: Object,
    lookups: Object,
  });
  const emit = defineEmits(['update:modelValue', 'saved']);
  const form = reactive({}),
    busy = ref(false),
    error = ref(''),
    workerSearch = ref('');
  const workers = computed(() => props.lookups?.['task-members'] || []);
  const filteredWorkers = computed(() => {
    const normalize = (value) =>
      String(value)
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
    return workers.value.filter((person) =>
      normalize(person.label).includes(normalize(workerSearch.value)),
    );
  });
  const required = [
    (v) => (v !== null && v !== undefined && String(v).trim().length > 0) || 'Campo obligatorio',
  ];
  watch(
    () => props.modelValue,
    (open) => {
      if (!open) return;
      const values = { ...props.preset, ...props.record };
      Object.assign(form, {
        title: values.title || '',
        assignee_ids: [
          ...new Set([...(values.member_ids || []), values.responsible_id].filter(Boolean)),
        ],
        due_date: values.due_date || '',
        description: values.description || '',
      });
      workerSearch.value = '';
      error.value = '';
    },
    { immediate: true },
  );
  async function save() {
    busy.value = true;
    error.value = '';
    try {
      const body = {
        title: form.title.trim(),
        due_date: form.due_date,
      };
      if (props.record || form.description.trim())
        body.description = form.description.trim() || null;
      if (props.record) body.revision = props.record.revision;
      else {
        body.responsible_id = form.assignee_ids[0];
        body.member_ids = form.assignee_ids.slice(1);
        if (props.preset?.parent_id) body.parent_id = props.preset.parent_id;
        if (props.preset?.project_id) body.project_id = props.preset.project_id;
        if (props.preset?.start_date) body.start_date = props.preset.start_date;
      }
      const result = await api('/tasks' + (props.record ? '/' + props.record.id : ''), {
        method: props.record ? 'PATCH' : 'POST',
        body,
      });
      emit('saved', result);
      emit('update:modelValue', false);
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
</script>
<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="(v) => emit('update:modelValue', v)"
    :persistent="busy"
  >
    <q-card class="record-form task-assignment-form">
      <q-card-section class="row items-center"
        ><div>
          <span class="eyebrow">{{ record ? 'ACTUALIZAR TAREA' : 'ASIGNAR TRABAJO' }}</span>
          <h2>{{ record ? 'Editar tarea' : 'Asignar tarea' }}</h2>
        </div>
        <q-space /><q-btn
          flat
          round
          icon="close"
          aria-label="Cerrar formulario"
          :disable="busy"
          v-close-popup
      /></q-card-section>
      <q-separator />
      <q-form @submit="save">
        <q-card-section>
          <div class="form-grid">
            <q-input
              v-model="form.title"
              outlined
              type="textarea"
              autogrow
              class="full-field"
              label="¿Qué debe hacer? *"
              maxlength="250"
              :rules="required"
            />
            <q-select
              v-model="form.assignee_ids"
              outlined
              emit-value
              map-options
              :label="record ? 'Personas asignadas' : 'Asignar a *'"
              :options="filteredWorkers"
              use-input
              multiple
              use-chips
              :readonly="Boolean(record)"
              input-debounce="0"
              @filter="
                (value, update) =>
                  update(() => {
                    workerSearch = value;
                  })
              "
              :rules="[(value) => value?.length > 0 || 'Selecciona al menos una persona']"
            />
            <q-input
              v-model="form.due_date"
              outlined
              type="date"
              label="Fecha límite *"
              :min="record?.start_date"
              :rules="required"
            />
            <q-input
              v-model="form.description"
              outlined
              type="textarea"
              autogrow
              class="full-field"
              label="Instrucciones (opcional)"
              maxlength="5000"
            />
          </div>
          <p class="info-note">
            {{
              record
                ? 'Los integrantes se conservan. Puedes añadir más personas desde la ficha de la tarea.'
                : 'Puedes seleccionar una o varias personas. Cada una verá la tarea en «Mis tareas» y podrá añadir sus propias evidencias.'
            }}
          </p>
          <q-banner v-if="error" class="error-banner q-mt-md" role="alert">{{ error }}</q-banner>
        </q-card-section>
        <q-card-actions align="right" class="q-pa-lg"
          ><q-btn flat no-caps label="Cancelar" :disable="busy" v-close-popup /><q-btn
            type="submit"
            color="primary"
            unelevated
            no-caps
            :label="record ? 'Guardar cambios' : 'Asignar tarea'"
            :loading="busy"
        /></q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>
