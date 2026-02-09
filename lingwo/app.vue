<script setup lang="ts">
import { Toaster } from 'vue-sonner'
import { Menu } from 'lucide-vue-next'
import { Sheet, SheetContent, SheetTrigger } from '~/components/ui/sheet'

useHead({
  htmlAttrs: {
    lang: 'ru'
  }
})

const { status } = useAuth()
const route = useRoute()

// Страницы, где не нужен sidebar
const pagesWithoutSidebar = ['/login', '/register', '/confirmation']

const showSidebar = computed(() => {
  return status.value === 'authenticated' && !pagesWithoutSidebar.includes(route.path)
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NuxtRouteAnnouncer />
    
    <!-- Layout with Sidebar for authenticated users -->
    <div v-if="showSidebar" class="flex min-h-screen">
      <!-- Desktop Sidebar (always visible on md and above) -->
      <aside class="hidden md:block border-r border-gray-200">
        <div class="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </aside>
      
      <!-- Mobile Sidebar (Sheet) -->
      <Sheet>
        <SheetTrigger as-child>
          <button
            class="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50 transition-colors"
            aria-label="Открыть меню"
          >
            <Menu :size="24" class="text-gray-700" />
          </button>
        </SheetTrigger>
        <SheetContent side="left" class="w-64 p-0 border-r border-gray-200">
          <Sidebar />
        </SheetContent>
      </Sheet>
      
      <main class="flex-1 min-w-0">
        <NuxtPage />
      </main>
    </div>
    
    <!-- Layout without Sidebar for guest pages -->
    <template v-else>
      <main class="flex-1">
        <NuxtPage />
      </main>
      
      <!-- Footer -->
      <footer class="bg-white border-t border-gray-200 py-6 mt-auto">
        <div class="container mx-auto px-10">
          <div class="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-600">
            <div class="flex items-center gap-2">
              <span class="font-medium text-primary">Лингво</span>
              <span>© {{ new Date().getFullYear() }}. Все права защищены.</span>
            </div>
            
            <div class="flex items-center gap-2">
              <span>Вопросы и предложения:</span>
              <a 
                href="mailto:contact@lingwo.ru" 
                class="text-primary hover:text-primary/80 font-medium transition-colors"
              >
                contact@lingwo.ru
              </a>
            </div>
          </div>
        </div>
      </footer>
    </template>
    
    <Toaster 
      position="top-right" 
      :toast-options="{
        style: { 
          background: 'white',
          color: '#1f2937',
          border: '1px solid #6DCE78'
        },
        class: 'sonner-toast',
      }"
    />
  </div>
</template>

<style>
.sonner-toast {
  box-shadow: 0 4px 12px rgba(109, 206, 120, 0.15) !important;
}
/* Специфичность выше scoped * на страницах, чтобы opacity и transform точно анимировались */
.page-enter-active,
.page-leave-active {
  transition-property: opacity, transform !important;
  transition-duration: 0.3s !important;
  transition-timing-function: ease-out !important;
}
.page-enter-from {
  opacity: 0 !important;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0 !important;
  transform: translateY(-6px);
}
.page-enter-to,
.page-leave-from {
  opacity: 1 !important;
  transform: translateY(0);
}
</style>
