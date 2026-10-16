<script setup>
  import SearchSelect from './SearchSelect.vue';
  import { ref, reactive, watch, computed } from 'vue';
  import { api, session } from '../api';
  import { human } from '../format';
  const props = defineProps({
    modelValue: Boolean,
    record: Object,
    resource: String,
    action: String,
    lookups: Object,
  });
  const emit = defineEmits(['update:modelValue', 'saved']);
  const form = reactive({}),
    busy = ref(false),
    error = ref('');
  const stageChoices = {
    elaboracion: ['revision'],
    revision: ['firma', 'observado'],
    firma: ['derivacion', 'observado'],
    derivacion: ['aprobado', 'atendido', 'observado'],
    observado: ['subsanacion'],
    subsanacion: ['revision', 'derivacion'],
  };
  const config = computed(
    () =>
      ({
        advance: {
          title: 'Añadir avance y evidencia',
          note: 'Cuenta lo que estás haciendo y comparte un enlace de Drive o Docs. La persona que revisa la tarea podrá consultar tu evidencia.',
          fields: [
            {
              key: 'comment',
              label: '¿Qué has realizado?',
              type: 'textarea',
            },
            { key: 'progress', label: 'Mi avance (%)', type: 'number' },
            { key: 'evidence_url', label: 'Enlace de la evidencia (Drive o Docs)' },
            {
              key: 'evidence_access',
              label: 'La persona que revisa la tarea puede abrir este enlace',
              type: 'boolean',
            },
          ],
        },
        participants: {
          title: 'Agregar participantes',
          note: 'Los integrantes actuales se conservan junto con su historial. Los nuevos participantes podrán registrar sus propios avances.',
          fields: [
            {
              key: 'member_ids',
              label: 'Integrantes que deseas agregar',
              lookup: 'task-members',
              multiple: true,
            },
          ],
        },
        close: {
          title: 'Validar y cerrar tarea',
          note: 'Selecciona la última versión validada de una evidencia vinculada. Si autorizas una excepción, registra una justificación de al menos 10 caracteres.',
          fields: [
            {
              key: 'evidence_version_id',
              label: 'Versión de evidencia validada',
              lookup: 'evidence-versions',
            },
            {
              key: 'justification',
              label: 'Justificación autorizada (opcional)',
              type: 'textarea',
            },
          ],
        },
        validate: {
          title: 'Validar evidencia',
          fields: [
            {
              key: 'status',
              label: 'Resultado',
              options: ['validada', 'observada'],
            },
            { key: 'note', label: 'Nota de validación', type: 'textarea' },
          ],
        },
        stage: {
          title: 'Registrar actuación del trámite',
          fields: [
            {
              key: 'status',
              label: 'Siguiente etapa',
              options: stageChoices[props.record?.status] || [],
            },
            { key: 'department', label: 'Dependencia externa actual' },
            { key: 'note', label: 'Actuación / observación', type: 'textarea' },
            {
              key: 'resolution_id',
              label: 'Resolución / documento de atención',
              lookup: 'documents',
            },
          ],
        },
        review: {
          title: 'Revisar entregable OS',
          fields: [
            {
              key: 'status',
              label: 'Resultado',
              options: ['en_revision', 'observado', 'conforme'],
            },
            { key: 'note', label: 'Revisión / observaciones', type: 'textarea' },
          ],
        },
        send: {
          title: 'Registrar envío del documento',
          note: 'Selecciona cómo se envió y registra la fecha real del envío.',
          fields: [
            { key: 'status', label: 'Medio de envío', options: (props.lookups?.['document-statuses']?.[props.record?.document_type_id] || ['enviado_digital', 'enviado_fisico', 'enviado_fisico_y_digital']).filter((state) => ['enviado_digital', 'enviado_fisico', 'enviado_fisico_y_digital', 'compartido', 'enviado'].includes(state)) },
            { key: 'sent_date', label: 'Fecha de envío', type: 'date' },
          ],
        },
        task: {
          title: 'Crear tarea desde el acuerdo',
          note: 'Se conservarán el proyecto, responsable y plazo del acuerdo. Las siguientes solicitudes abrirán la misma tarea.',
          fields: [],
        },
        activate: {
          title: 'Confirmar modelo o criterio revisado',
          note: 'La activación requiere validar la fuente, versión y aplicabilidad institucional. El catálogo de prueba contiene criterios ficticios.',
          fields: [],
        },
        revoke: {
          title: 'Retirar asignación',
          note: 'Se retirará esta asignación de rol o permiso. La actuación quedará en la bitácora.',
          fields: [],
        },
      })[props.action] || { title: 'Acción', fields: [] },
  );
  const visibleFields = computed(() =>
    config.value.fields.filter(
      (field) =>
        props.action !== 'advance' ||
        form.kind === 'avance' ||
        (!field.key.startsWith('evidence_') && field.key !== 'progress'),
    ),
  );
  function required(field) {
    const key = field.key;
    if (props.action === 'advance')
      return (
        ['progress', 'kind', 'comment'].includes(key) ||
        (form.kind === 'avance' && ['evidence_title', 'evidence_url'].includes(key))
      );
    if (props.action === 'participants') return key === 'member_ids';
    if (props.action === 'send') return ['status', 'sent_date'].includes(key);
    if (props.action === 'close')
      return key === 'evidence_version_id' && String(form.justification || '').trim().length < 10;
    if (['validate', 'review'].includes(props.action)) return ['status', 'note'].includes(key);
    if (props.action === 'stage')
      return (
        ['status', 'department', 'note'].includes(key) ||
        (key === 'resolution_id' && ['aprobado', 'atendido'].includes(form.status))
      );
    return false;
  }
  function rules(field) {
    const checks = [];
    if (required(field))
      checks.push(
        (v) =>
          (Array.isArray(v)
            ? v.length > 0
            : v !== null && v !== undefined && String(v).trim().length > 0) ||
          'Completa este campo.',
      );
    if (['note', 'evidence_title', 'justification'].includes(field.key)) {
      const min = field.key === 'justification' ? 10 : 3;
      checks.push(
        (v) => !v || String(v).trim().length >= min || `Ingresa al menos ${min} caracteres.`,
      );
    }
    if (field.key === 'progress')
      checks.push(
        (v) =>
          (Number.isInteger(Number(v)) && Number(v) >= 0 && Number(v) <= 100) ||
          'Ingresa un porcentaje entero entre 0 y 100.',
      );
    if (field.key === 'evidence_url')
      checks.push((v) => {
        if (!v) return true;
        try {
          const url = new URL(v);
          return (
            (url.protocol === 'https:' &&
              ['drive.google.com', 'docs.google.com'].includes(url.hostname) &&
              !url.username &&
              !url.password) ||
            'Usa un enlace HTTPS de Google Drive o Docs.'
          );
        } catch {
          return 'Usa un enlace HTTPS de Google Drive o Docs.';
        }
      });
    return checks;
  }
  watch(
    () => props.modelValue,
    (open) => {
      if (!open) return;
      Object.keys(form).forEach((k) => delete form[k]);
      form.progress =
        props.record?.participants?.find((p) => p.id === session.user?.id)?.reported_progress || 0;
      form.member_ids = [];
      form.evidence_access = false;
      form.kind = 'avance';
      form.request_review = false;
      form.department = props.record?.current_department || '';
      if (props.action === 'send') form.sent_date = new Date().toLocaleDateString('en-CA');
      error.value = '';
    },
  );
  async function save() {
    if (props.action === 'advance' && form.kind === 'avance' && !form.evidence_access) {
      error.value = 'Confirma que el jefe puede acceder a la evidencia antes de enviar el avance.';
      return;
    }
    busy.value = true;
    error.value = '';
    try {
      const body = {};
      for (const field of config.value.fields) {
        const v = form[field.key];
        if (v !== '' && v !== undefined && v !== null)
          body[field.key] = field.type === 'number' ? Number(v) : v;
      }
      if (props.action === 'advance') {
        body.kind = 'avance';
        body.evidence = {
          url: form.evidence_url,
          access_confirmed: form.evidence_access,
        };
        delete body.evidence_title;
        delete body.evidence_url;
        delete body.evidence_access;
      }
      let action = props.action === 'activate' ? 'validate' : props.action;
      let path = `/${props.resource}/${props.record.id}/${action}`;
      if (action === 'revoke') path = `/admin${path}`;
      if (!['validate', 'revoke'].includes(action) || props.action === 'activate')
        body.revision = props.record.revision;
      const result = await api(path, { method: 'POST', body });
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
    ><q-card class="action-form"
      ><q-card-section class="row items-center"
        ><h2>{{ config.title }}</h2>
        <q-space /><q-btn
          flat
          round
          icon="close"
          aria-label="Cerrar acción"
          v-close-popup
          :disable="busy" /></q-card-section
      ><q-form @submit="save"
        ><q-card-section
          ><p v-if="config.note" class="info-note">{{ config.note }}</p>
          <div class="q-gutter-y-md">
            <template v-for="field in visibleFields" :key="field.key"
              ><q-checkbox
                v-if="field.type === 'boolean'"
                v-model="form[field.key]"
                :label="field.label" /><SearchSelect use-input
                v-else-if="field.lookup"
                v-model="form[field.key]"
                outlined
                emit-value
                map-options
                clearable
                :label="field.label + (required(field) ? ' *' : '')"
                :rules="rules(field)"
                :options="lookups[field.lookup] || []"
                :multiple="field.multiple || false"
                :use-chips="field.multiple || false" /><SearchSelect use-input
                v-else-if="field.options"
                v-model="form[field.key]"
                outlined
                :label="field.label + (required(field) ? ' *' : '')"
                :options="field.options.map((value) => ({ value, label: human(value) }))"
                emit-value
                map-options
                :rules="rules(field)" /><q-input
                v-else
                v-model="form[field.key]"
                outlined
                :label="field.label + (required(field) ? ' *' : '')"
                :rules="rules(field)"
                :type="field.type || 'text'"
                :min="field.key === 'progress' ? 0 : undefined"
                :max="field.key === 'progress' ? 100 : undefined"
            /></template>
          </div>
          <q-btn
            v-if="action === 'participants'"
            class="q-mt-md"
            flat
            no-caps
            icon="groups"
            label="Agregar a todo el equipo"
            @click="form.member_ids = (lookups['task-members'] || []).map((p) => p.value)"
          />
          <q-banner v-if="error" class="error-banner q-mt-lg" role="alert">{{
            error
          }}</q-banner></q-card-section
        ><q-card-actions align="right" class="q-pa-lg"
          ><q-btn flat no-caps label="Cancelar" v-close-popup :disable="busy" /><q-btn
            type="submit"
            color="primary"
            unelevated
            no-caps
            :label="action === 'advance' ? 'Guardar avance y evidencia' : 'Confirmar acción'"
            :loading="busy" /></q-card-actions></q-form></q-card
  ></q-dialog>
</template>
