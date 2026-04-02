<template>
  <div class="dark">
    <AppLayout />
  </div>
</template>

<script setup lang="ts">
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import { useGlobalShortcuts } from '@/composables/useGlobalShortcuts'

// Initialize the singleton audio player once at the app root
useAudioPlayer()
useGlobalShortcuts()
</script>
