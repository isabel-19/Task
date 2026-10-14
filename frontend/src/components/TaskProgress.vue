<script setup>
  import { ref, watch } from 'vue';
  import { api, query } from '../api';
  import { dateLabel } from '../modules';
  import StatusBadge from './StatusBadge.vue';
  const props = defineProps({ record: Object });
  const emit = defineEmits(['saved']);
  const updates = ref([]),
    error = ref(''),
    busy = ref(false),
    total = ref(0),
    page = ref(1);
  const reviewing = ref(null),
    result = ref('validada'),
    note = ref('');
  let sequence = 0;
  async function load() {
    const turn = ++sequence;
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
    }
  }
  watch(
    () => [props.record.id, props.record.revision],
    () => {
      reviewing.value = null;
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
      await api('/task-updates/' + reviewing.value.id + '/review', {
        method: 'POST',
        body: { revision: props.record.revision, status: result.value, note: note.value },
      });
      reviewing.value = null;
      emit('saved');
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
</script>
<template>
  <section class="related-section task-progress-panel">
    <h3>Avances del equipo</h3>
    <p class="info-note">
      Reportado: {{ record.reported_progress }}% · Validado por el jefe:
      {{ record.validated_progress }}%. El avance de la tarea es el promedio validado de sus
      participantes.
    </p>
    <div class="team-progress-list">
      <div v-for="person in record.participants" :key="person.id" class="team-progress-person">
        <div>
          <b>{{ person.name }}</b
          ><small>{{ person.responsible ? 'Responsable' : 'Participante' }}</small>
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
    <h3 class="q-mt-lg">Historial de aportes y evidencias</h3>
    <p v-if="!updates.length" class="related-empty">
      Los participantes pueden registrar su primer avance con evidencia.
    </p>
    <article v-for="item in updates" :key="item.id" class="progress-entry">
      <div class="row items-center q-gutter-sm">
        <b>{{ item._labels?.author_id }}</b
        ><span>{{ item.progress }}%</span
        ><StatusBadge
          :value="item.kind === 'avance' ? item.review_status : item.kind"
        /><q-space /><small>{{ dateLabel(item.created_at) }}</small>
      </div>
      <p>{{ item.comment }}</p>
      <a v-if="item.url" :href="item.url" target="_blank" rel="noopener noreferrer"
        >Abrir evidencia <q-icon name="open_in_new"
      /></a>
      <p v-if="item.review_note" class="review-note">
        <b>{{ item.reviewer }}:</b> {{ item.review_note }}
      </p>
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
    </article>
    <q-pagination
      v-if="total > 20"
      v-model="page"
      :max="Math.ceil(total / 20)"
      :max-pages="5"
      class="q-my-md"
    />
    <q-form v-if="reviewing" class="progress-review-form q-gutter-y-md" @submit="review">
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
    <q-banner v-if="error" class="error-banner q-mt-md" role="alert">{{ error }}</q-banner>
  </section>
</template>
