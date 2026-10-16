<script setup>
  import { computed, ref, watch } from 'vue';
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
  // Etapas reales del flujo: asignación → avance → revisión por jefatura → cierre.
  const steps = [
    { key: 'pendiente', label: 'Asignada' },
    { key: 'en_progreso', label: 'En progreso' },
    { key: 'en_revision', label: 'En revisión' },
    { key: 'cerrada', label: 'Cerrada' },
  ];
  const currentStep = computed(() => Math.max(0, steps.findIndex((step) => step.key === props.record.status)));
  const nextStep = computed(() => {
    const status = props.record.status;
    if (status === 'cerrada')
      return { text: 'La tarea está cerrada. Consulta las evidencias registradas.', action: null };
    if (status === 'en_revision')
      return props.record.can_review
        ? {
            text: 'Revisa el avance de cada persona en Evidencias, valida o devuelve con nota y, cuando todos estén validados, cierra la tarea.',
            action: 'Revisar avances',
          }
        : { text: 'Esperando la validación de jefatura. No necesitas hacer nada más por ahora.', action: null };
    if (status === 'en_progreso')
      return props.record.can_advance
        ? { text: 'Registra tu avance con evidencia. Cuando todas las personas reporten 100 %, la tarea pasa a revisión.', action: 'Registrar mi avance' }
        : { text: 'Las personas asignadas registran su avance. Al llegar todas al 100 %, la tarea pasa a revisión.', action: null };
    return props.record.can_advance
      ? { text: 'Empieza registrando tu avance con evidencia.', action: 'Registrar mi avance' }
      : { text: 'Esperando que las personas asignadas registren su avance.', action: null };
  });
  function runNextStep() {
    tab.value = nextStep.value.action === 'Registrar mi avance' ? 'submit' : 'evidence';
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
        <section v-if="tab === 'summary'" class="task-flow" aria-label="Etapa de la tarea">
          <ol class="task-flow-steps">
            <li
              v-for="(step, index) in steps"
              :key="step.key"
              :class="{ done: index < currentStep, current: index === currentStep }"
              :aria-current="index === currentStep ? 'step' : undefined"
            >
              <span class="task-flow-dot">
                <q-icon v-if="index < currentStep" name="check" size="14px" />
                <template v-else>{{ index + 1 }}</template>
              </span>
              {{ step.label }}
            </li>
          </ol>
          <div class="task-flow-next">
            <p>
              <b>Siguiente paso:</b>
              {{ nextStep.text }}
            </p>
            <q-btn
              v-if="nextStep.action"
              color="primary"
              unelevated
              no-caps
              :label="nextStep.action"
              @click="runNextStep"
            />
          </div>
        </section>
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
  .task-flow {
    margin-bottom: 20px;
  }
  .task-flow-steps {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 18px;
    list-style: none;
    margin: 0 0 14px;
    padding: 0;
    font-size: 13px;
    color: var(--muted);
  }
  .task-flow-steps li {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .task-flow-steps li.current {
    color: var(--ink);
    font-weight: 600;
  }
  .task-flow-steps li.done {
    color: #15803d;
  }
  .task-flow-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 1px solid currentColor;
    font-size: 12px;
    font-weight: 600;
  }
  .task-flow-steps li.current .task-flow-dot {
    background: var(--teal);
    border-color: var(--teal);
    color: #fff;
  }
  .task-flow-steps li.done .task-flow-dot {
    background: #dcfce7;
    border-color: #86d4a4;
  }
  .task-flow-next {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 10px;
    background: #eaf1ff;
    color: #1e40af;
    font-size: 14px;
    line-height: 1.5;
  }
  .task-flow-next p {
    margin: 0;
    flex: 1 1 320px;
  }
</style>
