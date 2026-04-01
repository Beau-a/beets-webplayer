<template>
  <div class="dark">
    <AppLayout />
  </div>
</template>

<script setup lang="ts">
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAudioPlayer } from '@/composables/useAudioPlayer'

// Initialize the singleton audio player once at the app root
useAudioPlayer()
</script>
