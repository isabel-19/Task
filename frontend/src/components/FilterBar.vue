<script setup>
  import SearchSelect from './SearchSelect.vue';
  defineProps({
    modelValue: Object,
    lookups: Object,
    search: { type: Boolean, default: true },
    expanded: { type: Boolean, default: false },
    available: { type: Array, default: () => ['axis_id', 'process_id', 'responsible_id'] },
  });
  const emit = defineEmits(['update:modelValue']);
  function set(key, value, current) {
    emit('update:modelValue', { ...current, [key]: value ?? '' });
  }
</script>
<template>
  <div class="filter-bar">
    <q-input
      v-if="search"
      outlined
      dense
      :model-value="modelValue.q"
      placeholder="Buscar por nombre o número…"
      aria-label="Buscar registros"
      debounce="350"
      class="filter-search"
      @update:model-value="(v) => set('q', v, modelValue)"
      ><template #prepend><q-icon name="search" size="20px" /></template
    ></q-input>
    <SearchSelect use-input
      v-if="available.includes('axis_id')"
      outlined
      dense
      clearable
      emit-value
      map-options
      :model-value="modelValue.axis_id || null"
      :options="lookups.axes || []"
      label="Todos los ejes"
      class="filter-select"
      @update:model-value="(v) => set('axis_id', v, modelValue)"
    />
    <SearchSelect use-input
      outlined
      dense
      clearable
      emit-value
      map-options
      v-if="available.includes('responsible_id')"
      :model-value="modelValue.responsible_id || null"
      :options="lookups.users || []"
      label="Responsables"
      class="filter-select"
      @update:model-value="(v) => set('responsible_id', v, modelValue)"
    />
    <q-input
      outlined
      dense
      clearable
      :model-value="modelValue.year"
      label="Año"
      type="number"
      min="2000"
      max="2100"
      debounce="400"
      class="filter-year"
      @update:model-value="(v) => set('year', v, modelValue)"
    />
    <template v-if="expanded">
      <SearchSelect use-input
        outlined
        dense
        clearable
        emit-value
        map-options
        :model-value="modelValue.month || null"
        :options="
          Array.from({ length: 12 }, (_, i) => ({
            value: i + 1,
            label: new Intl.DateTimeFormat('es', { month: 'long' }).format(new Date(2026, i, 1)),
          }))
        "
        label="Mes"
        class="filter-select"
        @update:model-value="(v) => set('month', v, modelValue)"
      />
      <SearchSelect use-input
        outlined
        dense
        clearable
        emit-value
        map-options
        v-if="available.includes('process_id')"
        :model-value="modelValue.process_id || null"
        :options="lookups.processes || []"
        label="Proceso"
        class="filter-select"
        @update:model-value="(v) => set('process_id', v, modelValue)"
      />
      <q-input
        outlined
        dense
        clearable
        :model-value="modelValue.from"
        label="Plazo desde"
        type="date"
        class="filter-select"
        @update:model-value="(v) => set('from', v, modelValue)"
      />
      <q-input
        outlined
        dense
        clearable
        :model-value="modelValue.to"
        label="Plazo hasta"
        type="date"
        class="filter-select"
        @update:model-value="(v) => set('to', v, modelValue)"
      />
    </template>
  </div>
</template>
