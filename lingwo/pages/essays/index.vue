<script setup lang="ts">
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/vue-query'
import {
  FileText,
  Search,
  Calendar,
  Eye,
  Trash2,
  RotateCcw,
  BookOpen,
  GraduationCap,
  Filter,
} from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Label } from '~/components/ui/label'
import { Slider } from '~/components/ui/slider'
import { Skeleton } from '~/components/ui/skeleton'
import { toast } from 'vue-sonner'

useHead({
  title: 'Мои сочинения - Лингво',
})

interface CriterionItem {
  score: number
  comment?: string
  found_in_text?: string[]
  suggestions?: string[]
}

interface EssayListItem {
  id: number
  type: string
  theme: string
  ended_at: string
  total_score: number
  total_score_per: number | null
  max_score: number | null
  criteries?: Record<string, CriterionItem>
  excerpt?: string
}

const { status, data: session } = useAuth()
const config = useRuntimeConfig()
const queryClient = useQueryClient()

// Фильтры
const sortOrder = ref<'date' | 'score' | 'theme'>('date')
const searchQuery = ref('')
const scoreRange = ref([0, 100])
const typeFilter = ref<'all' | 'essay' | 'ege'>('all')
const sectionFilter = ref<string>('all')

const { data: essaysRaw, isLoading: essaysLoading } = useQuery({
  queryKey: computed(() => [
    'essays-list',
    session.value?.accessToken ?? '',
    sortOrder.value,
    searchQuery.value,
    typeFilter.value,
  ]),
  queryFn: async (): Promise<EssayListItem[]> => {
    const token = session.value?.accessToken
    if (!token) return []
    const params = new URLSearchParams()
    params.set('order', sortOrder.value)
    params.set('limit', '200')
    if (searchQuery.value.trim()) params.set('search', searchQuery.value.trim())
    if (typeFilter.value !== 'all') params.set('type_filter', typeFilter.value)
    const url = `${config.public.baseApiURL}/essays?${params.toString()}`
    return await $fetch<EssayListItem[]>(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
  enabled: computed(() => status.value === 'authenticated' && !!session.value?.accessToken),
  placeholderData: keepPreviousData,
})

const allEssays = computed(() => essaysRaw.value ?? [])

// Фильтр по диапазону баллов (процент 0–100)
const filteredEssays = computed(() => {
  let list = [...allEssays.value]
  const [minP, maxP] = scoreRange.value
  list = list.filter((e) => {
    const p = e.total_score_per != null ? Math.round(e.total_score_per * 100) : 0
    return p >= minP && p <= maxP
  })
  if (sectionFilter.value !== 'all') {
    list = list.filter((e) => e.type === sectionFilter.value)
  }
  return list
})

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function starsCount(essay: EssayListItem) {
  if (essay.total_score_per == null) return null
  const p = essay.total_score_per * 100
  if (p >= 90) return 5
  if (p >= 70) return 4
  if (p >= 50) return 3
  if (p >= 30) return 2
  return 1
}

function scoreLabel(essay: EssayListItem) {
  if (essay.max_score != null && essay.max_score > 0) {
    return `${Math.round(essay.total_score)} / ${Math.round(essay.max_score)}`
  }
  if (essay.total_score_per != null) {
    return `${Math.round(essay.total_score_per * 100)}%`
  }
  return '—'
}

async function deleteEssay(essay: EssayListItem) {
  const token = session.value?.accessToken
  if (!token) return
  try {
    await $fetch(`${config.public.baseApiURL}/essay/${essay.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    await queryClient.invalidateQueries({ queryKey: ['essays-list'] })
    await queryClient.invalidateQueries({ queryKey: ['essays'] })
    toast.success('Сочинение удалено')
  } catch (e: unknown) {
    toast.error(e && typeof e === 'object' && 'data' in e ? String((e as { data?: { detail?: string } }).data?.detail) : 'Не удалось удалить')
  }
}

function repeatTheme(essay: EssayListItem) {
  navigateTo({
    path: '/essay/new',
    query: { theme: essay.theme, type: essay.type },
  })
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-green-50/30 to-emerald-50/40">
    <div class="container mx-auto px-4 py-8 max-w-6xl">
      <div class="space-y-6">
        <!-- Заголовок -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <FileText class="h-4 w-4 text-primary" />
              </div>
              Мои сочинения
            </CardTitle>
            <CardDescription class="text-gray-600">
              Просматривайте, фильтруйте и повторяйте свои работы
            </CardDescription>
          </CardHeader>
        </Card>

        <template v-if="status === 'authenticated'">
          <!-- Панель фильтров -->
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2 text-base">
                <Filter class="h-4 w-4 text-primary" />
                Фильтры
              </CardTitle>
            </CardHeader>
            <CardContent class="flex flex-col gap-6">
              <!-- Сортировка -->
              <div class="space-y-2">
                <Label class="text-sm font-medium text-gray-700">Сортировка</Label>
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
                    :class="sortOrder === 'date' ? 'border-primary bg-primary text-white hover:bg-primary/90' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                    @click="sortOrder = 'date'"
                  >
                    По дате
                  </button>
                  <button
                    type="button"
                    class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
                    :class="sortOrder === 'score' ? 'border-primary bg-primary text-white hover:bg-primary/90' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                    @click="sortOrder = 'score'"
                  >
                    По баллу
                  </button>
                  <button
                    type="button"
                    class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
                    :class="sortOrder === 'theme' ? 'border-primary bg-primary text-white hover:bg-primary/90' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                    @click="sortOrder = 'theme'"
                  >
                    По теме
                  </button>
                </div>
              </div>

              <!-- Поиск -->
              <div class="space-y-2">
                <Label for="search" class="text-sm font-medium text-gray-700">Поиск по тексту и теме</Label>
                <div class="flex h-10 w-full items-stretch overflow-hidden rounded-md border border-gray-200 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
                  <span class="flex w-10 shrink-0 items-center justify-center text-muted-foreground">
                    <Search class="h-4 w-4" aria-hidden="true" />
                  </span>
                  <input
                    id="search"
                    v-model="searchQuery"
                    type="text"
                    placeholder="Введите фразу из сочинения или тему..."
                    class="min-w-0 flex-1 border-0 bg-transparent px-2 py-2 text-sm outline-none placeholder:text-muted-foreground"
                  />
                </div>
              </div>

              <!-- Диапазон баллов -->
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label class="text-sm font-medium text-gray-700">Диапазон баллов (%)</Label>
                  <span class="text-sm font-semibold text-primary">
                    {{ scoreRange[0] }} – {{ scoreRange[1] }}%
                  </span>
                </div>
                <div class="pt-3">
                  <Slider
                    v-model="scoreRange"
                    :min="0"
                    :max="100"
                    :step="5"
                    class="w-full"
                  />
                </div>
              </div>

              <!-- Тип: итоговое / ЕГЭ -->
              <div class="space-y-2">
                <Label class="text-sm font-medium text-gray-700">Тип работы</Label>
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1.5"
                    :class="typeFilter === 'all' ? 'border-primary bg-primary text-white hover:bg-primary/90' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                    @click="typeFilter = 'all'"
                  >
                    Все
                  </button>
                  <button
                    type="button"
                    class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1.5"
                    :class="typeFilter === 'essay' ? 'border-primary bg-primary text-white hover:bg-primary/90' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                    @click="typeFilter = 'essay'"
                  >
                    <BookOpen class="h-4 w-4" />
                    Итоговое сочинение
                  </button>
                  <button
                    type="button"
                    class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1.5"
                    :class="typeFilter === 'ege' ? 'border-primary bg-primary text-white hover:bg-primary/90' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                    @click="typeFilter = 'ege'"
                  >
                    <GraduationCap class="h-4 w-4" />
                    ЕГЭ
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Список карточек -->
          <div v-if="essaysLoading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Card v-for="i in 6" :key="i" class="border-green-100/50 bg-white shadow-lg">
              <CardHeader>
                <Skeleton class="h-5 w-3/4" />
                <Skeleton class="h-4 w-24 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton class="h-4 w-full mb-4" />
                <Skeleton class="h-4 w-2/3" />
              </CardContent>
            </Card>
          </div>

          <template v-else>
            <p v-if="filteredEssays.length === 0" class="text-center text-muted-foreground py-12">
              Нет сочинений по заданным фильтрам. Измените фильтры или напишите новое сочинение.
            </p>
            <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Card
                v-for="essay in filteredEssays"
                :key="essay.id"
                class="border-green-100/50 bg-white shadow-lg transition-shadow hover:shadow-xl"
              >
                <CardHeader class="pb-2">
                  <div class="flex flex-wrap items-center gap-2 mb-1.5">
                    <span
                      class="inline-flex items-center gap-2 rounded-md px-3 py-1 text-xs font-medium border shrink-0"
                      :class="essay.type === 'ege' ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'"
                    >
                      <GraduationCap v-if="essay.type === 'ege'" class="h-4 w-4 shrink-0" />
                      <BookOpen v-else class="h-4 w-4 shrink-0" />
                      {{ essay.type === 'ege' ? 'ЕГЭ' : 'Итоговое сочинение' }}
                    </span>
                  </div>
                  <CardTitle class="text-base font-semibold text-gray-800 line-clamp-2">
                    {{ essay.theme }}
                  </CardTitle>
                  <CardDescription class="flex items-center gap-1.5 text-sm">
                    <Calendar class="h-3.5 w-3.5 shrink-0" />
                    {{ formatDate(essay.ended_at) }}
                  </CardDescription>
                </CardHeader>
                <CardContent class="space-y-4">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-gray-700">Балл:</span>
                    <span class="font-semibold text-primary">{{ scoreLabel(essay) }}</span>
                    <span v-if="starsCount(essay) != null" class="flex gap-0.5 items-center" :title="`${starsCount(essay)} из 5`">
                      <span
                        v-for="n in 5"
                        :key="n"
                        class="text-lg leading-none"
                        :class="n <= (starsCount(essay) ?? 0) ? 'text-amber-400' : 'text-gray-200'"
                      >
                        {{ n <= (starsCount(essay) ?? 0) ? '★' : '☆' }}
                      </span>
                    </span>
                  </div>
                  <p class="text-sm text-gray-600 line-clamp-3 min-h-[3.75rem]">
                    {{ essay.excerpt || 'Текст пока не загружен.' }}
                    <span v-if="essay.excerpt && essay.excerpt.length >= 150">…</span>
                  </p>
                  <div class="flex flex-wrap gap-2">
                    <NuxtLink :to="`/essays/${essay.id}`" class="flex-1 min-w-0">
                      <Button
                        size="sm"
                        class="w-full bg-primary text-white border-primary hover:bg-primary/90 hover:text-white"
                        title="Детали"
                      >
                        <Eye class="mr-0 h-3.5 w-3.5 shrink-0 xl:mr-1.5" />
                        <span class="hidden xl:inline">Детали</span>
                      </Button>
                    </NuxtLink>
                    <Button
                      size="sm"
                      variant="outline"
                      class="border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300"
                      @click="deleteEssay(essay)"
                    >
                      <Trash2 class="h-3.5 w-3.5 shrink-0" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      class="border-primary/30 text-primary hover:bg-primary/10"
                      @click="repeatTheme(essay)"
                    >
                      <RotateCcw class="mr-1.5 h-3.5 w-3.5 shrink-0" />
                      Повторить
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </template>
        </template>

        <Card v-else class="border-green-100/50 bg-white shadow-lg">
          <CardContent class="py-12 text-center text-muted-foreground">
            Войдите в аккаунт, чтобы видеть свои сочинения.
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  transition-property: transform, box-shadow, background-color, border-color;
  transition-duration: 0.2s;
  transition-timing-function: ease-in-out;
}
</style>
