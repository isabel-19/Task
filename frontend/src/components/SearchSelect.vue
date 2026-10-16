<script>
  // q-select que filtra mientras se escribe, sin distinguir mayúsculas ni tildes.
  // Recibe las mismas props y eventos que q-select y reenvía sus slots.
  export default { inheritAttrs: false };
  // Coincidencia sin mayúsculas ni tildes; las opciones pueden ser texto u objetos con etiqueta.
  export function matchesSearch(option, query, optionLabel = 'label') {
    const normalize = (text) =>
      String(text ?? '')
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .toLowerCase()
        .trim();
    const label = option !== null && typeof option === 'object' ? option[optionLabel] : option;
    return normalize(label).includes(normalize(query));
  }
</script>
<script setup>
  import { computed, ref } from 'vue';
  const props = defineProps({
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: 'label' },
  });
  const search = ref('');
  const visibleOptions = computed(() => {
    if (!search.value.trim()) return props.options;
    return props.options.filter((option) => matchesSearch(option, search.value, props.optionLabel));
  });
  function onFilter(value, update) {
    update(() => {
      search.value = value;
    });
  }
</script>
<template>
  <q-select
    v-bind="$attrs"
    :options="visibleOptions"
    use-input
    @filter="onFilter"
    @popup-hide="search = ''"
  >
    <template v-for="(_, name) in $slots" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps || {}" />
    </template>
  </q-select>
</template>
