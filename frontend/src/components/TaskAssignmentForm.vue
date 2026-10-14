<script setup>
  import { reactive, ref, computed, watch } from 'vue';
  import { api, session } from '../api';
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
    extra = ref(false);
  const workers = computed(() => props.lookups?.['task-members'] || []);
  const project = computed(() =>
    (props.lookups?.projects || []).find(
      (p) => p.value === (props.record?.project_id || props.preset?.project_id),
    ),
  );
  const themes = computed(() => {
    const values = [...(props.lookups?.['task-themes'] || props.lookups?.axes || [])];
    if (form.axis_id && !values.some((v) => v.value === form.axis_id)) {
      const legacy = props.lookups?.axes?.find((v) => v.value === form.axis_id);
      if (legacy) values.push(legacy);
    }
    return values;
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
        axis_id:
          values.axis_id ||
          project.value?.axis_id ||
          ((props.lookups?.['task-themes'] || []).length === 1
            ? props.lookups['task-themes'][0].value
            : null),
        responsible_id: values.responsible_id || session.user?.id || null,
        due_date: values.due_date || new Date().toLocaleDateString('en-CA'),
        office: values.office || null,
        member_ids: (values.member_ids || []).filter((id) => id !== values.responsible_id),
        description: values.description || '',
      });
      extra.value = Boolean(form.description);
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
        axis_id: form.axis_id,
        responsible_id: form.responsible_id,
        due_date: form.due_date,
        office: form.office || null,
      };
      if (props.record || form.description.trim())
        body.description = form.description.trim() || null;
      if (props.record) body.revision = props.record.revision;
      else {
        body.member_ids = form.member_ids;
        if (props.preset?.parent_id) body.parent_id = props.preset.parent_id;
        if (props.preset?.project_id && project.value?.axis_id === form.axis_id)
          body.project_id = props.preset.project_id;
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
          <span class="eyebrow">{{ record ? 'ACTUALIZAR ACTIVIDAD' : 'ASIGNAR TRABAJO' }}</span>
          <h2>{{ record ? 'Editar actividad / tarea' : 'Nueva actividad / tarea' }}</h2>
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
            <q-select
              v-model="form.axis_id"
              outlined
              emit-value
              map-options
              label="Temática / eje *"
              :options="themes"
              :rules="required"
              :disable="Boolean(record?.parent_id || preset?.parent_id)"
            />
            <q-input
              v-model="form.title"
              outlined
              type="textarea"
              autogrow
              class="full-field"
              label="Actividad / tarea *"
              maxlength="250"
              :rules="required"
            />
            <q-select
              v-model="form.responsible_id"
              outlined
              emit-value
              map-options
              label="Responsable *"
              :options="workers"
              :rules="required"
            />
            <q-input
              v-model="form.due_date"
              outlined
              type="date"
              label="Plazo (Deadline) *"
              :min="record?.start_date"
              :rules="required"
            />
            <div class="full-field">
              <q-select
                v-model="form.member_ids"
                outlined
                multiple
                use-chips
                emit-value
                map-options
                label="Apoyo / participantes"
                :options="workers"
                :readonly="Boolean(record)"
              />
              <q-btn
                v-if="!record"
                flat
                no-caps
                icon="groups"
                label="Asignar a todo el equipo"
                @click="form.member_ids = workers.map((p) => p.value)"
              />
            </div>
            <q-select
              v-model="form.office"
              outlined
              emit-value
              map-options
              clearable
              label="Oficina (si aplica)"
              :options="lookups?.offices || []"
            />
          </div>
          <q-expansion-item
            v-model="extra"
            label="Observaciones / instrucciones (opcional)"
            icon="notes"
            class="q-mt-md"
          >
            <q-input
              v-model="form.description"
              outlined
              type="textarea"
              label="Observaciones / instrucciones"
              class="q-mt-sm"
            />
          </q-expansion-item>
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
