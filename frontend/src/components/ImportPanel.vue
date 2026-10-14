<script setup>
  import { ref, reactive, computed } from 'vue';
  import { api } from '../api';
  const props = defineProps({ meta: Object, lookups: Object });
  const emit = defineEmits(['imported']);
  const entity = ref('documents'),
    file = ref(null),
    sheet = ref(''),
    source = ref(null),
    preview = ref(null),
    busy = ref(false),
    error = ref(''),
    confirmed = ref(false);
  const mapping = reactive({}),
    constants = reactive({});
  const allowed = [
    'projects',
    'tasks',
    'documents',
    'meetings',
    'agreements',
    'service-orders',
    'deliverables',
    'indicators',
    'indicator-results',
  ];
  const fields = computed(() => props.meta[entity.value]?.fields || []);
  async function body() {
    if (!file.value) throw new Error('Selecciona un archivo CSV o XLSX.');
    if (file.value.size > 5000000) throw new Error('Máximo 5 MB por archivo.');
    const bytes = new Uint8Array(await file.value.arrayBuffer());
    let binary = '';
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    return {
      filename: file.value.name,
      content_base64: btoa(binary),
      entity: entity.value,
      sheet: sheet.value || null,
    };
  }
  async function inspect() {
    busy.value = true;
    error.value = '';
    preview.value = null;
    confirmed.value = false;
    try {
      source.value = await api('/import/preview', { method: 'POST', body: await body() });
      sheet.value = source.value.sheet;
      Object.keys(mapping).forEach((k) => delete mapping[k]);
      Object.keys(constants).forEach((k) => delete constants[k]);
      for (const f of fields.value) {
        const exact = source.value.headers.find((h) => [f.key, f.label.toLowerCase()].includes(h));
        if (exact) mapping[f.key] = exact;
      }
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
  async function validate() {
    busy.value = true;
    error.value = '';
    try {
      const mapped = Object.fromEntries(Object.entries(mapping).filter(([, v]) => v));
      const fixed = Object.fromEntries(
        Object.entries(constants).filter(([, v]) => v !== '' && v !== null && v !== undefined),
      );
      preview.value = await api('/import/preview', {
        method: 'POST',
        body: { ...(await body()), mapping: mapped, constants: fixed },
      });
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
  async function commit() {
    busy.value = true;
    error.value = '';
    try {
      const result = await api('/import/commit/' + preview.value.id, { method: 'POST', body: {} });
      preview.value.imported = result.imported;
      emit('imported');
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
</script>
<template>
  <q-card-section
    ><p class="info-note">
      La fuente se conserva como respaldo con SHA-256. La importación valida encabezados,
      referencias y duplicados antes de guardar. No se modifican los archivos originales.
    </p>
    <div class="form-grid">
      <q-select
        v-model="entity"
        outlined
        emit-value
        map-options
        label="Destino"
        :options="allowed.filter((e) => meta[e]).map((e) => ({ value: e, label: meta[e].label }))"
        @update:model-value="
          source = null;
          preview = null;
        "
      /><q-file
        v-model="file"
        outlined
        label="Fuente CSV UTF-8 / XLSX · máximo 5 MB"
        accept=".csv,.xlsx"
        @update:model-value="
          source = null;
          preview = null;
        "
      /><q-select
        v-if="source?.sheets.length > 1"
        v-model="sheet"
        outlined
        label="Hoja"
        :options="source.sheets"
        @update:model-value="inspect"
      />
    </div>
    <q-btn
      color="primary"
      outline
      no-caps
      label="Leer encabezados"
      icon="table_view"
      :loading="busy"
      @click="inspect"
    /><template v-if="source"
      ><h3 class="q-mt-lg">Mapeo de columnas · {{ source.row_count }} filas</h3>
      <p class="muted">
        Selecciona una columna de la fuente o un valor constante. Las relaciones deben usar
        registros que ya existen.
      </p>
      <div v-for="field in fields" :key="field.key" class="import-map-row">
        <b>{{ field.label }}{{ field.required ? ' *' : '' }}</b
        ><q-select
          v-model="mapping[field.key]"
          dense
          outlined
          clearable
          :options="source.headers"
          label="Columna de origen"
        /><q-select
          v-if="field.lookup"
          v-model="constants[field.key]"
          dense
          outlined
          clearable
          emit-value
          map-options
          :options="lookups[field.lookup] || []"
          label="Registro constante"
        /><q-select
          v-else-if="field.options?.length"
          v-model="constants[field.key]"
          dense
          outlined
          clearable
          :options="field.options"
          label="Valor constante"
        /><q-input v-else v-model="constants[field.key]" dense outlined label="Valor constante" />
      </div>
      <q-btn
        class="q-mt-lg"
        color="primary"
        no-caps
        unelevated
        label="Validar y previsualizar"
        :loading="busy"
        @click="validate"
      />
      <div v-if="source.external_links.length" class="q-mt-lg info-note">
        <b>Enlaces externos encontrados: {{ source.external_links.length }}</b>
        <p v-for="(link, i) in source.external_links" :key="i">
          {{ link.url }} · Pendiente de revisión; no se ha leído ni importado.
        </p>
      </div></template
    ><template v-if="preview"
      ><div class="import-summary q-mt-lg">
        <b>{{ preview.valid_count }} filas válidas</b><span>{{ preview.error_count }} errores</span
        ><small>SHA-256: {{ preview.sha256 }}</small>
      </div>
      <div v-if="preview.errors.length" class="error-banner q-pa-md q-my-md">
        <p v-for="item in preview.errors" :key="item.row">
          Fila {{ item.row }}:
          {{ typeof item.error === 'string' ? item.error : JSON.stringify(item.error) }}
        </p>
        <p>
          Corrige la copia de trabajo y vuelve a generar la previsualización. La fuente respaldada
          se conserva.
        </p>
      </div>
      <pre class="json-value">{{ JSON.stringify(preview.rows.slice(0, 5), null, 2) }}</pre>
      <q-checkbox
        v-if="!preview.imported"
        v-model="confirmed"
        label="Revisé el mapeo y las filas; importaré estos registros en el entorno actual."
      /><q-btn
        v-if="!preview.imported"
        class="q-mt-md"
        color="primary"
        unelevated
        no-caps
        label="Confirmar importación"
        :disable="!confirmed || !!preview.error_count || !preview.valid_count"
        :loading="busy"
        @click="commit"
      /><q-banner v-else class="success-banner q-mt-md"
        >Se importaron {{ preview.imported }} registros. La trazabilidad conserva archivo, hoja y
        fila.</q-banner
      ></template
    ><q-banner v-if="error" class="error-banner q-mt-lg" role="alert">{{
      error
    }}</q-banner></q-card-section
  >
</template>
