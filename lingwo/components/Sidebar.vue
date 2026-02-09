<script setup lang="ts">
import {
  LayoutDashboard,
  FileEdit,
  FileText,
  BookOpen,
  Settings,
  Info,
  LogOut
} from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import SheetClose from '~/components/ui/sheet/SheetClose.vue'
import { inject } from 'vue'

const { data, signOut } = useAuth()

// Проверяем, находимся ли мы внутри Sheet через provide/inject
const isInSheet = inject('isInSheet', false)

const navigationItems = [
  {
    label: 'Главная',
    icon: LayoutDashboard,
    href: '/'
  },
  {
    label: 'Новое сочинение',
    icon: FileEdit,
    href: '/essay/new'
  },
  {
    label: 'Мои сочинения',
    icon: FileText,
    href: '/essays'
  },
  // {
  //   label: 'Тренировка по темам',
  //   icon: BookOpen,
  //   href: '/practice'
  // },
  {
    label: 'Настройки',
    icon: Settings,
    href: '/settings'
  },
  {
    label: 'О проекте',
    icon: Info,
    href: '/about'
  }
]

const route = useRoute()
const isActive = (href: string) => {
  if (href === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(href)
}

const handleLogout = async () => {
  await signOut({ callbackUrl: '/login' })
}

const getUserInitial = () => {
  const name = data.value?.user?.name || 'П'
  return name.charAt(0).toUpperCase()
}

const getUserName = () => {
  return data.value?.user?.name || 'Пользователь'
}
</script>

<template>
  <aside class="flex flex-col h-screen w-64 bg-white shadow-sm">
    <!-- Логотип -->
    <div class="flex items-center justify-center px-6 py-5 border-b border-gray-200">
      <NuxtImg 
        src="/assets/logo.svg" 
        alt="Лингво" 
        width="150" 
        height="150"
        class="shrink-0"
      />
    </div>

    <!-- Навигация -->
    <nav class="flex-1 overflow-y-auto px-3 py-4 space-y-1">
      <template v-for="item in navigationItems" :key="item.href">
        <!-- На мобильных (внутри Sheet) оборачиваем в SheetClose -->
        <SheetClose v-if="isInSheet" as-child>
          <NuxtLink
            :to="item.href"
            :class="[
              'group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
              isActive(item.href)
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                'shrink-0',
                isActive(item.href) ? 'text-primary' : 'text-gray-500 group-hover:text-gray-700'
              ]"
              :size="20"
            />
            <span
              :class="[
                'text-sm font-medium',
                isActive(item.href) ? 'text-primary' : 'text-gray-900'
              ]"
            >
              {{ item.label }}
            </span>
          </NuxtLink>
        </SheetClose>
        <!-- На десктопе обычная ссылка -->
        <NuxtLink
          v-else
          :to="item.href"
          :class="[
            'group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
            isActive(item.href)
              ? 'bg-primary/10 text-primary border border-primary/20'
              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
          ]"
        >
          <component
            :is="item.icon"
            :class="[
              'shrink-0',
              isActive(item.href) ? 'text-primary' : 'text-gray-500 group-hover:text-gray-700'
            ]"
            :size="20"
          />
          <span
            :class="[
              'text-sm font-medium',
              isActive(item.href) ? 'text-primary' : 'text-gray-900'
            ]"
          >
            {{ item.label }}
          </span>
        </NuxtLink>
      </template>
    </nav>

    <!-- Блок пользователя -->
    <div class="border-t border-gray-200 p-4">
      <DropdownMenu>
        <DropdownMenuTrigger
          class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-gray-100 transition-colors outline-none focus:ring-2 focus:ring-primary/20"
        >
          <div
            class="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-semibold text-sm shrink-0"
          >
            {{ getUserInitial() }}
          </div>
          <div class="flex-1 min-w-0 text-left">
            <div class="text-sm font-medium text-gray-900 truncate">
              {{ getUserName() }}
            </div>
            <div class="text-xs text-gray-500 truncate">
              Профиль
            </div>
          </div>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-56">
          <DropdownMenuItem
            @click="handleLogout"
            class="text-red-600 focus:text-red-600 focus:bg-red-50 cursor-pointer"
          >
            <LogOut :size="16" class="mr-2" />
            Выйти из профиля
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </aside>
</template>

<style scoped>
/* Стили для скроллбара */
nav::-webkit-scrollbar {
  width: 6px;
}

nav::-webkit-scrollbar-track {
  background: transparent;
}

nav::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

nav::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>