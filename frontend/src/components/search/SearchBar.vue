<template>
  <div class="search-bar">
    <div class="search-inner">
      <!-- Search icon -->
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>

      <input
        ref="inputEl"
        v-model="localValue"
        type="text"
        class="search-input"
        :placeholder="placeholder"
        @input="onInput"
        @keydown.escape="clearSearch"
      />

      <!-- Clear button -->
      <button
        v-if="localValue"
        class="clear-btn"
        @click="clearSearch"
        aria-label="Clear search"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="clear-icon">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: string
  placeholder?: string
  debounceMs?: number
}>(), {
  modelValue: '',
  placeholder: 'Search your library... (try artist:radiohead year:2000..2010)',
  debounceMs: 300,
})

const emit = defineEmits<{
  search: [query: string]
  'update:modelValue': [value: string]
}>()

const inputEl = ref<HTMLInputElement | null>(null)
const localValue = ref(props.modelValue)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(() => props.modelValue, (val) => {
  if (val !== localValue.value) {
    localValue.value = val
  }
})

function onInput() {
  emit('update:modelValue', localValue.value)
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('search', localValue.value)
  }, props.debounceMs)
}

function clearSearch() {
  localValue.value = ''
  emit('update:modelValue', '')
  emit('search', '')
  inputEl.value?.focus()
}
</script>

<style scoped>
.search-bar {
  width: 100%;
}

.search-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: #27272a; /* zinc-800 */
  border-radius: 10px;
  padding: 0 14px;
  transition: box-shadow 0.15s;
}

.search-inner:focus-within {
  box-shadow: 0 0 0 2px #7c3aed; /* violet-700 */
}

.search-icon {
  width: 18px;
  height: 18px;
  color: #71717a; /* zinc-500 */
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #f4f4f5; /* zinc-100 */
  padding: 12px 0;
  min-width: 0;
}

.search-input::placeholder {
  color: #52525b; /* zinc-600 */
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: #71717a;
  transition: color 0.15s;
  flex-shrink: 0;
}

.clear-btn:hover {
  color: #a1a1aa;
}

.clear-icon {
  width: 16px;
  height: 16px;
}
</style>
