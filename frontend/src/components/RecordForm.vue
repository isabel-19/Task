<script setup>
  import { reactive, ref, watch } from 'vue';
  import { api, session } from '../api';
  import TaskAssignmentForm from './TaskAssignmentForm.vue';
  const props = defineProps({
    modelValue: Boolean,
    resource: String,
    schema: Object,
    record: Object,
    preset: Object,
    lookups: Object,
  });
  const emit = defineEmits(['update:modelValue', 'saved']);
  const form = reactive({}),
    busy = ref(false),
    error = ref('');
  watch(
    () => props.modelValue,
    (open) => {
      if (!open) return;
      Object.keys(form).forEach((k) => delete form[k]);
      error.value = '';
      if (props.resource === 'tasks') form.member_ids = [];
      for (const field of props.schema?.fields || []) {
        form[field.key] =
          props.record?.[field.key] ??
          props.preset?.[field.key] ??
          (props.resource === 'tasks' && field.key === 'responsible_id'
            ? session.user?.id
            : null) ??
          field.default ??
          (field.type === 'boolean'
            ? false
            : field.type === 'date'
              ? new Date().toLocaleDateString('en-CA')
              : field.key === 'year'
                ? new Date().getFullYear()
                : field.key === 'version' && field.type === 'number'
                  ? 1
                  : '');
      }
    },
  );
  async function save() {
    busy.value = true;
    error.value = '';
    try {
      const body = {};
      for (const field of props.schema.fields) {
        let value = form[field.key];
        if (field.key === 'password' && !value && props.record) continue;
        if (value === '' || value === undefined || value === null) {
          if (props.record && field.nullable) body[field.key] = null;
          continue;
        }
        if (field.type === 'number') value = Number(value);
        body[field.key] = value;
      }
      if (props.resource === 'tasks' && !props.record) body.member_ids = form.member_ids;
      if (props.record) body.revision = props.record.revision;
      const result = await api('/' + props.resource + (props.record ? '/' + props.record.id : ''), {
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
  function rules(field) {
    return field.required
      ? [(v) => (v !== '' && v !== null && v !== undefined) || 'Campo obligatorio']
      : [];
  }
</script>
<template>
  <TaskAssignmentForm
    v-if="resource === 'tasks'"
    :model-value="modelValue"
    :record="record"
    :preset="preset"
    :lookups="lookups"
    @update:model-value="(v) => emit('update:modelValue', v)"
    @saved="(result) => emit('saved', result)"
  />
  <q-dialog
    v-else
    :model-value="modelValue"
    @update:model-value="(v) => emit('update:modelValue', v)"
    :persistent="busy"
    ><q-card class="record-form"
      ><q-card-section class="row items-center"
        ><div>
          <span class="eyebrow">{{ record ? 'ACTUALIZAR REGISTRO' : 'NUEVO REGISTRO' }}</span>
          <h2>{{ schema?.label }}</h2>
        </div>
        <q-space /><q-btn
          flat
          round
          icon="close"
          aria-label="Cerrar formulario"
          :disable="busy"
          v-close-popup /></q-card-section
      ><q-separator /><q-form @submit="save"
        ><q-card-section
          ><p v-if="resource === 'evidence-links'" class="info-note">
            Selecciona una evidencia y exactamente un destino: tarea, documento, acuerdo, reunión,
            proyecto o indicador.
          </p>
          <p v-if="resource.includes('versions')" class="info-note">
            Las versiones son inmutables. Verifica el número de versión y los permisos del enlace
            antes de guardar.
          </p>
          <div class="form-grid">
            <template v-for="field in schema?.fields" :key="field.key"
              ><q-checkbox
                v-if="field.type === 'boolean'"
                v-model="form[field.key]"
                :label="field.label" /><q-select
                v-else-if="field.lookup"
                v-model="form[field.key]"
                outlined
                emit-value
                map-options
                clearable
                :label="field.label + (field.required ? ' *' : '')"
                :options="
                  lookups[
                    resource === 'tasks' && field.key === 'responsible_id'
                      ? 'task-members'
                      : field.lookup
                  ] || []
                "
                :rules="rules(field)" /><q-select
                v-else-if="field.options?.length"
                v-model="form[field.key]"
                outlined
                clearable
                :label="field.label + (field.required ? ' *' : '')"
                :options="field.options"
                :rules="rules(field)" /><q-input
                v-else
                v-model="form[field.key]"
                outlined
                :label="field.label + (field.required ? ' *' : '')"
                :type="
                  field.type === 'datetime'
                    ? 'datetime-local'
                    : ['date', 'number', 'password'].includes(field.type)
                      ? field.type
                      : ['description', 'agenda'].includes(field.key)
                        ? 'textarea'
                        : 'text'
                "
                :rules="rules(field)"
                :class="{
                  'full-field': ['description', 'agenda', 'url', 'source_url'].includes(field.key),
                }"
                :step="field.type === 'number' ? 'any' : undefined"
            /></template>
          </div>
          <div v-if="resource === 'tasks' && !record" class="q-gutter-y-md q-mt-md">
            <q-select
              v-model="form.member_ids"
              outlined
              multiple
              use-chips
              emit-value
              map-options
              label="Otros participantes de la tarea"
              :options="lookups['task-members'] || []"
            />
            <q-btn
              flat
              no-caps
              icon="groups"
              label="Asignar a todo el equipo"
              @click="form.member_ids = (lookups['task-members'] || []).map((p) => p.value)"
            />
            <p class="info-note">
              El responsable y los participantes verán esta tarea en su espacio. Cada persona
              reporta su avance con evidencia y el jefe lo revisa.
            </p>
          </div>
          <q-banner v-if="error" class="error-banner" role="alert" style="white-space: pre-wrap">{{
            error
          }}</q-banner></q-card-section
        ><q-card-actions align="right" class="q-pa-lg"
          ><q-btn flat no-caps label="Cancelar" v-close-popup :disable="busy" /><q-btn
            color="primary"
            unelevated
            no-caps
            label="Guardar registro"
            type="submit"
            :loading="busy" /></q-card-actions></q-form></q-card
  ></q-dialog>
</template>
