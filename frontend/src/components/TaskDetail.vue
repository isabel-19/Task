<script setup>
  import { ref, watch } from 'vue';
  import { dateLabel } from '../modules';
  import StatusBadge from './StatusBadge.vue';
  import TaskProgress from './TaskProgress.vue';
  import TaskEvidenceForm from './TaskEvidenceForm.vue';
  import TaskAssigner from './TaskAssigner.vue';
  const props = defineProps({
    modelValue: Boolean,
    record: Object,
    uploadOptions: Object,
    initialTab: { type: String, default: 'summary' },
  });
  const emit = defineEmits(['update:modelValue', 'edit', 'participants', 'saved']);
  const tab = ref('summary');
  watch(
    [() => props.modelValue, () => props.record.id, () => props.initialTab],
    () => {
      if (props.modelValue)
        tab.value =
          props.initialTab === 'submit' && !props.record.can_advance
            ? 'evidence'
            : props.initialTab;
    },
    { immediate: true },
  );
  function submitted(value) {
    tab.value = 'evidence';
    emit('saved', value);
  }
</script>
<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <q-card class="record-detail task-detail">
      <q-card-section class="detail-heading">
        <div>
          <span class="eyebrow">TAREA ASIGNADA</span>
          <h2>{{ record.title }}</h2>
          <TaskAssigner :record="record" />
          <StatusBadge :value="record.status" />
        </div>
        <q-btn flat round icon="close" aria-label="Cerrar detalle" v-close-popup />
      </q-card-section>
      <q-separator />
      <q-tabs
        v-model="tab"
        align="left"
        active-color="primary"
        indicator-color="primary"
        no-caps
        class="task-detail-tabs"
      >
        <q-tab name="summary" label="Resumen" icon="assignment" />
        <q-tab
          name="evidence"
          :label="`Evidencias (${(record.evidence_count || 0) + (record.document_count || 0)})`"
          icon="folder_open"
        />
        <q-tab
          v-if="record.can_advance"
          name="submit"
          label="Añadir evidencia"
          icon="attach_file"
        />
      </q-tabs>
      <q-card-section>
        <div v-if="tab === 'summary'" class="detail-grid task-summary">
          <div>
            <span class="detail-label">Personas asignadas</span>
            <p class="detail-value">
              {{
                record.participants?.map((person) => person.name).join(', ') ||
                record._labels?.responsible_id
              }}
            </p>
          </div>
          <div>
            <span class="detail-label">Fecha límite</span>
            <p class="detail-value">{{ dateLabel(record.due_date) }}</p>
          </div>
          <div v-if="record.description" class="full-field">
            <span class="detail-label">Instrucciones</span>
            <p class="detail-value task-instructions">{{ record.description }}</p>
          </div>
        </div>
        <div v-if="tab === 'summary'" class="detail-actions q-mt-lg">
          <q-btn
            color="primary"
            unelevated
            no-caps
            icon="folder_open"
            label="Ver evidencias"
            @click="tab = 'evidence'"
          />
          <q-btn
            v-if="record.can_advance"
            color="primary"
            outline
            no-caps
            icon="attach_file"
            label="Añadir mi evidencia"
            @click="tab = 'submit'"
          />
          <q-btn
            v-if="record.can_assign"
            outline
            color="primary"
            no-caps
            icon="group_add"
            label="Añadir personas"
            @click="emit('participants')"
          />
          <q-btn
            v-if="record.can_edit"
            outline
            color="primary"
            no-caps
            icon="edit"
            label="Editar tarea"
            @click="emit('edit')"
          />
        </div>
        <TaskEvidenceForm
          v-if="modelValue && tab === 'submit' && record.can_advance"
          :record="record"
          :upload-options="uploadOptions"
          @saved="submitted"
        />
        <p v-if="tab === 'summary' && record.status === 'cerrada'" class="info-note">
          Esta tarea está cerrada. Puedes consultar las evidencias registradas.
        </p>
        <p v-else-if="tab === 'summary'" class="info-note">
          Cada persona asignada añade sus evidencias entrando con su propia cuenta en «Mis tareas».
          Aquí puedes consultar los aportes del equipo.
        </p>
        <TaskProgress
          v-if="modelValue && tab === 'evidence'"
          :record="record"
          @saved="(value) => emit('saved', value)"
        />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>
<style scoped>
  .task-instructions {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
  .task-summary {
    margin-top: 0;
  }
</style>
