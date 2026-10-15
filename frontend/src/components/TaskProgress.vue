<script setup>
  import { ref, watch, computed } from 'vue';
  import { api, query } from '../api';
  import { dateLabel } from '../modules';
  import StatusBadge from './StatusBadge.vue';
  import EvidenceAttachment from './EvidenceAttachment.vue';
  const props = defineProps({ record: Object });
  const emit = defineEmits(['saved']);
  const updates = ref([]),
    error = ref(''),
    loading = ref(true),
    busy = ref(false),
    total = ref(0),
    page = ref(1);
  const reviewing = ref(null),
    result = ref('validada'),
    note = ref('');
  const closing = ref(false);
  const single = computed(() => (props.record.participants?.length || 0) <= 1);
  const closeEvidence = computed(
    () =>
      updates.value.find(
        (item) =>
          item.kind === 'avance' && item.review_status === 'validada' && item.evidence_version_id,
      )?.evidence_version_id,
  );
  let sequence = 0;
  async function load() {
    const turn = ++sequence;
    loading.value = true;
    try {
      const response = await api(
        '/task-updates?' +
          query({
            task_id: props.record.id,
            page: page.value,
            page_size: 20,
            scope: props.record.can_review ? 'team' : 'personal',
          }),
      );
      if (turn !== sequence) return;
      updates.value = response.items;
      total.value = response.total;
      error.value = '';
    } catch (e) {
      if (turn === sequence) error.value = e.message;
    } finally {
      if (turn === sequence) loading.value = false;
    }
  }
  watch(
    () => [props.record.id, props.record.revision],
    () => {
      reviewing.value = null;
      closing.value = false;
      page.value = 1;
      load();
    },
    { immediate: true },
  );
  watch(page, load);
  async function review() {
    busy.value = true;
    error.value = '';
    try {
      const record = await api('/task-updates/' + reviewing.value.id + '/review', {
        method: 'POST',
        body: { revision: props.record.revision, status: result.value, note: note.value },
      });
      reviewing.value = null;
      emit('saved', record);
      window.dispatchEvent(new Event('ogc:task-review-changed'));
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
  async function closeTask() {
    busy.value = true;
    error.value = '';
    try {
      const record = await api('/tasks/' + props.record.id + '/close', {
        method: 'POST',
        body: { revision: props.record.revision, evidence_version_id: closeEvidence.value },
      });
      closing.value = false;
      emit('saved', record);
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
</script>
<template>
  <section class="related-section task-progress-panel">
    <h3>{{ single ? 'Avance del responsable' : 'Avances de los participantes' }}</h3>
    <p class="info-note">
      Avance reportado: {{ record.reported_progress || 0 }}% · Validado:
      {{ record.validated_progress || 0 }}%
    </p>
    <q-linear-progress
      v-if="single"
      :value="(record.reported_progress || 0) / 100"
      rounded
      size="8px"
      class="q-mb-lg"
    />
    <q-expansion-item v-else label="Avance por persona" icon="groups" class="task-person-progress">
      <div class="team-progress-list">
        <div v-for="person in record.participants" :key="person.id" class="team-progress-person">
          <div>
            <b>{{ person.name }}</b
            ><small>Persona asignada</small>
          </div>
          <div>
            <small
              >Reportado {{ person.reported_progress }}% · Validado
              {{ person.validated_progress }}%</small
            ><q-linear-progress :value="person.validated_progress / 100" rounded size="8px" />
          </div>
          <StatusBadge :value="person.review_status" />
        </div>
      </div>
    </q-expansion-item>
    <section v-if="record.attachments?.length" class="linked-task-files">
      <h3>Documentos y evidencias vinculados</h3>
      <article
        v-for="file in record.attachments"
        :key="`${file.kind}-${file.id}`"
        class="progress-entry"
      >
        <b>{{ file.title }}</b>
        <p>
          {{ file.kind === 'document' ? 'Documento de Registro Digital' : 'Evidencia vinculada' }}
        </p>
        <EvidenceAttachment
          v-if="file.url"
          :url="file.url"
          :file="file.file"
          :label="file.kind === 'document' ? 'Abrir documento' : 'Abrir evidencia'"
        />
        <p v-else class="muted">Todavía no se registró un enlace para este archivo.</p>
      </article>
    </section>
    <h3 class="q-mt-lg">Avances y evidencias</h3>
    <q-linear-progress v-if="loading" indeterminate class="q-my-md" aria-label="Cargando avances" />
    <p v-else-if="!updates.length && !error" class="related-empty">
      Todavía no hay avances. Cada persona asignada puede registrar lo que está haciendo y su
      evidencia desde esta tarea.
    </p>
    <article v-for="item in updates" :key="item.id" class="progress-entry">
      <div class="row items-center q-gutter-sm">
        <b>{{ item._labels?.author_id }}</b
        ><span v-if="item.kind === 'avance'">{{ item.progress }}%</span
        ><StatusBadge
          :value="
            item.kind === 'avance'
              ? item.superseded
                ? 'envio_anterior'
                : item.review_status === 'pendiente'
                  ? 'pendiente_revision'
                  : item.review_status
              : item.kind
          "
        /><q-space /><small>{{ dateLabel(item.created_at) }}</small>
      </div>
      <div class="submission-description">
        <small>{{
          item.kind === 'avance' ? 'Descripción de la entrega' : 'Comentario del participante'
        }}</small>
        <p>{{ item.comment }}</p>
      </div>
      <EvidenceAttachment
        v-if="item.url"
        :url="item.url"
        :file="item.file"
        label="Abrir evidencia"
      />
      <div v-if="item.review_note" class="chief-review">
        <b><q-icon name="fact_check" /> Revisión de jefatura · {{ item.reviewer }}</b>
        <p>{{ item.review_note }}</p>
      </div>
      <div
        v-else-if="item.kind === 'avance' && !item.superseded"
        class="review-waiting"
        role="status"
      >
        <q-icon name="schedule" /> Pendiente de revisión por jefatura. La respuesta aparecerá aquí.
      </div>
      <q-btn
        v-if="item.can_review"
        class="q-ml-md"
        outline
        no-caps
        color="primary"
        label="Revisar avance"
        @click="
          reviewing = item;
          result = 'validada';
          note = '';
        "
      />
      <q-form
        v-if="reviewing?.id === item.id"
        class="progress-review-form q-gutter-y-md"
        @submit="review"
      >
        <b>Revisar el aporte de {{ reviewing._labels?.author_id }} ({{ reviewing.progress }}%)</b>
        <p class="info-note">
          Abre la evidencia y revisa el aporte antes de confirmar. Una observación permite enviar un
          nuevo avance con la corrección.
        </p>
        <q-select
          v-model="result"
          outlined
          label="Resultado de la revisión"
          :options="[
            { label: 'Validar avance', value: 'validada' },
            { label: 'Dejar observaciones', value: 'observada' },
          ]"
          emit-value
          map-options
        />
        <q-input
          v-model="note"
          outlined
          type="textarea"
          label="Nota del jefe *"
          :rules="[(v) => v.trim().length >= 3 || 'Describe la revisión']"
        />
        <q-btn type="submit" color="primary" no-caps label="Guardar revisión" :loading="busy" />
        <q-btn flat no-caps label="Cancelar" :disable="busy" @click="reviewing = null" />
      </q-form>
    </article>
    <q-pagination
      v-if="total > 20"
      v-model="page"
      :max="Math.ceil(total / 20)"
      :max-pages="5"
      class="q-my-md"
    />

    <q-banner v-if="error" class="error-banner q-mt-md" role="alert"
      >{{ error
      }}<template #action><q-btn flat no-caps label="Reintentar" @click="load" /></template
    ></q-banner>
    <div
      v-if="
        record.can_review && record.all_complete && record.status === 'en_revision' && closeEvidence
      "
      class="q-mt-lg"
    >
      <q-btn
        v-if="!closing"
        color="primary"
        no-caps
        label="Cerrar tarea"
        icon="task_alt"
        @click="closing = true"
      />
      <div v-else class="q-gutter-sm">
        <p>Los avances están validados al 100 %. ¿Deseas dar por terminada esta tarea?</p>
        <q-btn
          color="primary"
          no-caps
          label="Confirmar cierre"
          :loading="busy"
          @click="closeTask"
        />
        <q-btn flat no-caps label="Cancelar" :disable="busy" @click="closing = false" />
      </div>
    </div>
  </section>
</template>
