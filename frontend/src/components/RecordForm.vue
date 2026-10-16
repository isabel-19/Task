<script setup>
  import SearchSelect from './SearchSelect.vue';
  import { computed, reactive, ref, watch } from 'vue';
  import { api, query, session } from '../api';
  import { human } from '../format';
  import TaskAssignmentForm from './TaskAssignmentForm.vue';
  import { isSent, statusOptions } from '../documentWorkflow';
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
  const isDocument = computed(() => props.resource === 'documents');
  const automaticNumber = ref(false),
    numberPreview = ref(null),
    numberLoading = ref(false),
    numberError = ref('');
  let numberRequest = 0;
  let numberInput = null;
  // Switching numbering on or off must clear a message left by the previous mode.
  watch(automaticNumber, () => numberInput?.resetValidation());
  const documentStates = computed(() => {
    const states = statusOptions(props.lookups, form.document_type_id,
      props.schema?.fields?.find((field) => field.key === 'preparation_status')?.options || []);
    const legacy = props.record?.preparation_status;
    return legacy && ['elaborado', 'remitido', 'enviado'].includes(legacy) && !states.includes(legacy)
      ? [...states, legacy] : states;
  });
  const isMinutes = computed(() => documentStates.value.includes('en_reunion'));
  const visibleFields = computed(() => {
    const fields = props.schema?.fields || [];
    if (!isDocument.value) return fields;
    const order = ['document_type_id', 'section', 'number', 'axis_id', 'title', 'reference_text', 'date', 'sender', 'recipient', 'responsible_id', 'drafting_assistant_id', 'intake_format', 'notebook_number', 'preparation_status', 'sent_date', 'due_date', 'priority', 'followup_frequency', 'receipt_number', 'attended', 'email_url', 'comments'];
    return fields.filter((field) => !['url', 'access_confirmed', 'project_id', 'reference_id', 'year', 'email_url'].includes(field.key) &&
      !(field.key === 'sender' && form.section === 'emitidos') &&
      field.key !== 'sent_date' &&
      !(field.key === 'preparation_status' && form.section !== 'emitidos') &&
      !(['intake_format', 'notebook_number'].includes(field.key) && form.section !== 'recibidos') &&
      !(field.key === 'drafting_assistant_id' && !isMinutes.value))
      .map((field) => ({ ...field, label: ({ title: 'Asunto del documento', axis_id: 'Eje temático',
        date: form.section === 'recibidos' ? 'Fecha de recepción' : isMinutes.value ? 'Fecha de reunión' : 'Fecha del documento',
        responsible_id: isMinutes.value ? 'Representante OGC en la reunión' : form.section === 'emitidos' ? 'Remitente (personal OGC)' : 'Responsable de atención OGC',
        sender: 'Entidad remitente', recipient: isMinutes.value ? 'Unidad orgánica que convocó a reunión' : form.section === 'recibidos' ? 'Unidad orgánica a la que se derivó' : 'Destinatario / oficina',
        due_date: isMinutes.value ? 'Fecha límite para compartir el acta' : form.section === 'emitidos' ? 'Fecha límite de respuesta' : 'Fecha límite de atención',
        comments: isMinutes.value ? 'Seguimiento a acuerdos / comentarios' : 'Comentarios / tareas pendientes',
      })[field.key] || field.label,
      options: field.key === 'preparation_status' ? documentStates.value : field.options,
      required: form.section === 'emitidos'
        ? ['document_type_id', 'title', 'recipient'].includes(field.key) || (field.key === 'due_date' && form.followup_needed)
        : field.required }))
      .sort((a, b) => order.indexOf(a.key) - order.indexOf(b.key));
  });
  // A letter needs only type, subject and recipient; the rest sits under "Más detalles".
  // Follow-up fields appear only when the document says it expects a reply.
  const coreKeys = ['document_type_id', 'number', 'title', 'date', 'recipient'];
  const followKeys = ['due_date', 'followup_frequency'];
  const followupCheckbox = { key: 'followup_needed', type: 'boolean', label: 'Este documento necesita seguimiento (espera respuesta)' };
  const fieldSections = computed(() => {
    const fields = visibleFields.value;
    if (!isDocument.value || form.section !== 'emitidos') return [{ key: 'all', fields, collapsible: false }];
    const core = fields.filter((field) => coreKeys.includes(field.key));
    const follow = fields.filter((field) => followKeys.includes(field.key));
    const details = fields.filter((field) => !coreKeys.includes(field.key) && !followKeys.includes(field.key));
    return [
      { key: 'core', fields: [...core, followupCheckbox], collapsible: false },
      { key: 'follow', fields: form.followup_needed ? follow : [], collapsible: false },
      { key: 'details', title: 'Más detalles (opcionales)', fields: details, collapsible: true },
    ].filter((section) => section.fields.length);
  });
  const officeSearch = reactive({ recipient: '', sender: '' });
  function officeOptions(key) {
    const options = [...(props.lookups?.['document-recipients'] || [])];
    const previous = props.record?.[key];
    if (previous && !options.some((option) => option.value === previous)) options.push({ value: previous, label: previous });
    const normalize = (value) => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    return options.filter((option) => normalize(option.label).includes(normalize(officeSearch[key])));
  }
  const hasDocumentLink = computed(() => isDocument.value && props.schema?.fields.some((field) => field.key === 'url'));
  // The button opens only links that already pass the same rule that guards saving.
  const openableLink = computed(() => Boolean(form.url?.trim()) && linkRule(form.url) === true);
  watch(
    () => props.modelValue,
    (open) => {
      if (!open) return;
      Object.keys(form).forEach((k) => delete form[k]);
      error.value = '';
      numberPreview.value = null;
      numberError.value = '';
      automaticNumber.value = isDocument.value && !props.record;
      officeSearch.recipient = '';
      officeSearch.sender = '';
      if (props.resource === 'tasks') form.member_ids = [];
      if (props.resource === 'meetings') form.attendee_ids = [];
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
              ? (isDocument.value && field.nullable ? '' : new Date().toLocaleDateString('en-CA'))
              : field.key === 'year'
                ? new Date().getFullYear()
                : field.key === 'version' && field.type === 'number'
                  ? 1
                  : '');
      }
      form.followup_needed = Boolean(props.record?.followup_frequency && props.record.followup_frequency !== 'no_es_necesario');
      if (isDocument.value && !props.record) {
        if ('section' in form) form.section = props.preset?.section || 'emitidos';
        if ('responsible_id' in form) form.responsible_id = props.preset?.responsible_id || session.user?.id || '';
        if ('document_type_id' in form) form.document_type_id = props.preset?.document_type_id ||
          props.lookups?.['document-types']?.find((type) => type.label.toLowerCase() === 'carta')?.value || '';
      }
    },
  );
  watch(() => form.followup_needed, (value) => {
    if (value && !form.followup_frequency) form.followup_frequency = 'semanal';
  });
  watch(() => form.date, (value) => {
    if (isDocument.value && !props.record && /^\d{4}-\d{2}-\d{2}$/.test(value)) form.year = Number(value.slice(0, 4));
  });
  watch(() => [form.document_type_id, form.section], () => {
    if (!props.modelValue || !isDocument.value || form.section !== 'emitidos') return;
    const legacyUnchanged = props.record?.document_type_id === form.document_type_id &&
      props.record?.preparation_status === form.preparation_status;
    if (!legacyUnchanged && documentStates.value.length && !documentStates.value.includes(form.preparation_status)) {
      form.preparation_status = documentStates.value[0];
    }
  });
  watch(() => form.preparation_status, (value) => {
    if (isDocument.value && form.section === 'emitidos' && !isSent(value)) form.sent_date = '';
  });
  watch(
    () => [props.modelValue, form.document_type_id, form.year, form.section],
    async () => {
      const request = ++numberRequest;
      numberLoading.value = false;
      numberError.value = '';
      if (!props.modelValue || !isDocument.value || props.record) return;
      numberPreview.value = null;
      automaticNumber.value = false;
      if (!form.document_type_id || !Number.isInteger(Number(form.year)) || Number(form.year) < 1) return;
      numberLoading.value = true;
      try {
        const result = await api('/documents/next-number?' + query({
          document_type_id: form.document_type_id, year: form.year, section: form.section,
        }));
        if (request !== numberRequest) return;
        numberPreview.value = result;
        automaticNumber.value = result.automatic;
      } catch (e) {
        if (request === numberRequest) numberError.value = e.message;
      } finally {
        if (request === numberRequest) numberLoading.value = false;
      }
    },
  );
  async function save() {
    busy.value = true;
    error.value = '';
    try {
      const body = {};
      for (const field of props.schema.fields) {
        if (isDocument.value && !['year', 'url', 'access_confirmed'].includes(field.key) &&
          !visibleFields.value.some((visible) => visible.key === field.key)) continue;
        if (isDocument.value && (['project_id', 'reference_id'].includes(field.key) ||
          (field.key === 'sender' && form.section === 'emitidos'))) continue;
        if (isDocument.value && !props.record && automaticNumber.value && field.key === 'number') continue;
        let value = form[field.key];
        if (field.key === 'password' && !value && props.record) continue;
        if (value === '' || value === undefined || value === null) {
          if (props.record && field.nullable) body[field.key] = null;
          continue;
        }
        if (field.type === 'number') value = Number(value);
        body[field.key] = value;
      }
      // Hidden follow-up fields must be cleared explicitly, or an old deadline would survive the save.
      if (isDocument.value && form.section === 'emitidos' && !form.followup_needed) {
        body.followup_frequency = null;
        body.due_date = null;
      }
      if (isDocument.value && !props.record) body.automatic_number = automaticNumber.value;
      if (props.resource === 'tasks' && !props.record) body.member_ids = form.member_ids;
      if (props.resource === 'meetings' && !props.record) body.attendee_ids = form.attendee_ids;
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
    if (isDocument.value && field.key === 'number') {
      return automaticNumber.value && !props.record ? [] : [(v) => !!String(v || '').trim() || 'Ingresa el número o código original.'];
    }
    if (isDocument.value && field.key === 'email_url') return [(v) => {
      if (!v) return true;
      try { const url = new URL(v); return (url.protocol === 'https:' && !url.username && !url.password) || 'Usa un enlace HTTPS válido.'; }
      catch { return 'Usa un enlace HTTPS válido.'; }
    }];
    return field.required
      ? [(v) => (v !== null && v !== undefined && String(v).trim() !== '') || 'Campo obligatorio']
      : [];
  }
  function linkRule(value) {
    if (!value?.trim()) return true;
    try {
      const link = new URL(value.trim());
      return (link.protocol === 'https:' && !link.username && !link.password &&
        (['drive.google.com', 'docs.google.com', 'unajma.edu.pe'].includes(link.hostname) || link.hostname.endsWith('.unajma.edu.pe'))) ||
        'Usa un enlace HTTPS de Drive, Docs o UNAJMA.';
    } catch {
      return 'Pega la dirección completa del documento, empezando por https://.';
    }
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
          <q-banner v-if="numberError" class="error-banner q-mb-md" role="alert">{{ numberError }}</q-banner>
          <q-checkbox v-if="isDocument && !record && numberPreview?.automatic" v-model="automaticNumber"
            label="Asignar número automáticamente" class="q-mb-md" />
          <template v-for="section in fieldSections" :key="section.key">
          <component :is="section.collapsible ? 'q-expansion-item' : 'div'"
            v-bind="section.collapsible ? { label: section.title, class: 'record-more', headerClass: 'record-more-header' } : { class: 'record-section' }">
          <div class="form-grid">
            <template v-for="field in section.fields" :key="field.key"
              ><q-select hide-bottom-space
                v-if="isDocument && ['recipient', 'sender'].includes(field.key)"
                v-model="form[field.key]" outlined emit-value map-options clearable use-input fill-input hide-selected
                :input-debounce="150" :label="field.label + (field.required ? ' *' : '')"
                :options="officeOptions(field.key)" :rules="rules(field)"
                @filter="(value, update) => update(() => officeSearch[field.key] = value)"
                ><template #no-option><q-item><q-item-section>No hay oficinas que coincidan.</q-item-section></q-item></template></q-select
              ><q-checkbox
                v-else-if="field.type === 'boolean'"
                v-model="form[field.key]"
                :class="{ 'full-field': field.key === 'followup_needed' }"
                :label="field.label" /><SearchSelect use-input hide-bottom-space
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
                :rules="rules(field)" /><SearchSelect use-input hide-bottom-space
                v-else-if="field.options?.length"
                v-model="form[field.key]"
                outlined
                clearable
                :label="field.label + (field.required ? ' *' : '')"
                :options="field.options.map((value) => ({ value, label: human(value) }))"
                emit-value
                map-options
                :rules="rules(field)" /><q-input hide-bottom-space
                v-else
                :ref="(el) => { if (field.key === 'number') numberInput = el; }"
                :model-value="isDocument && field.key === 'number' && automaticNumber && !record ? numberPreview?.number || '' : form[field.key]"
                @update:model-value="(value) => form[field.key] = value"
                :readonly="isDocument && field.key === 'number' && automaticNumber && !record"
                :hint="isDocument && field.key === 'number' && automaticNumber && !record ? 'El número definitivo se asigna al guardar, según el tipo y el año del documento.' : undefined"
                outlined
                :label="field.label + (field.required ? ' *' : '')"
                :type="
                  field.type === 'datetime'
                    ? 'datetime-local'
                    : ['date', 'number', 'password'].includes(field.type)
                      ? field.type
                      : ['description', 'agenda', 'comments'].includes(field.key)
                        ? 'textarea'
                        : 'text'
                "
                :rules="rules(field)"
                :class="{
                  'full-field': ['description', 'agenda', 'url', 'source_url', 'comments', 'email_url'].includes(field.key) || (isDocument && field.key === 'title'),
                }"
                :step="field.type === 'number' ? 'any' : undefined"
            /></template>
          </div>
          </component>
          </template>
          <section v-if="hasDocumentLink" class="document-link-panel">
            <div class="document-link-heading">
              <span class="document-link-icon"><q-icon name="link" size="20px" /></span>
              <div>
                <h3>Documento digital</h3>
                <p>Pega el enlace de tu archivo de Drive o Docs.</p>
              </div>
            </div>
            <div class="document-link-row">
              <q-input v-model="form.url" outlined dense label="Enlace del documento" placeholder="https://drive.google.com/…"
                type="url" :rules="[linkRule]" hide-bottom-space class="document-link-input" />
              <q-btn v-if="openableLink" :href="form.url.trim()" target="_blank" rel="noopener noreferrer"
                outline no-caps color="primary" icon="open_in_new" label="Abrir enlace" class="document-link-open" />
            </div>
            <q-checkbox v-if="form.url" v-model="form.access_confirmed" dense label="Confirmo que el equipo OGC puede abrir el enlace" />
            <p class="document-link-note">Admitidos: Google Drive, Google Docs o sitio institucional de UNAJMA. {{ record ? 'Si cambias el enlace, se guarda una nueva versión y se conserva la anterior.' : 'El enlace se guardará como la primera versión del documento. También puedes completar el registro sin enlace y agregarlo después.' }}</p>
          </section>
          <div v-if="resource === 'tasks' && !record" class="q-gutter-y-md q-mt-md">
            <SearchSelect use-input hide-bottom-space hide-selected
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
          <div v-if="resource === 'meetings' && !record" class="q-gutter-y-md q-mt-md">
            <SearchSelect use-input hide-bottom-space hide-selected
              v-model="form.attendee_ids"
              outlined
              multiple
              use-chips
              emit-value
              map-options
              label="Asistentes"
              :options="lookups['users'] || []"
            />
            <p class="info-note">
              Cada asistente recibirá un aviso en la campana de alertas y verá la reunión en su espacio.
              Si cambias la fecha, el lugar o la reunión se cancela, también se avisa.
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
            :disable="numberLoading || !!numberError"
            :loading="busy" /></q-card-actions></q-form></q-card
  ></q-dialog>
</template>
