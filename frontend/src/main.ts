import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'

import './style.css'
import App from './App.vue'

const pinia = createPinia()

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/library' },
    { path: '/library', component: () => import('./views/LibraryView.vue') },
    { path: '/library/:albumId', component: () => import('./views/AlbumDetailView.vue') },
    { path: '/artist/:artistName', component: () => import('./views/ArtistView.vue') },
    { path: '/search', component: () => import('./views/SearchView.vue') },
    { path: '/import', component: () => import('./views/ImportView.vue') },
    { path: '/queue', component: () => import('./views/QueueView.vue') },
    { path: '/settings', component: () => import('./views/SettingsView.vue') },
  ],
})

createApp(App)
  .use(pinia)
  .use(router)
  .use(PrimeVue, {
    theme: {
      preset: Aura,
      options: {
        darkModeSelector: '.dark',
      },
    },
  })
  .mount('#app')
