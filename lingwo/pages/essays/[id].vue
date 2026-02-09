<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { FileText, Calendar, ArrowLeft, BookOpen, GraduationCap, Target, FileEdit, RotateCcw } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Skeleton } from '~/components/ui/skeleton'

interface CriterionItem {
  score: number
  comment?: string
  found_in_text?: string[]
  suggestions?: string[]
}

interface EssayDetail {
  id: number
  type: string
  theme: string
  text: string
  started_at: string
  ended_at: string
  total_score: number
  total_score_per: number | null
  max_score: number | null
  criteries?: Record<string, CriterionItem>
  common_mistakes?: string[]
}

definePageMeta({
  middleware: 'auth',
})

const route = useRoute()
const { status, data: session } = useAuth()
const config = useRuntimeConfig()

const essayId = computed(() => {
  const id = route.params.id
  const n = Number(id)
  return Number.isFinite(n) ? n : null
})

const { data: essay, isLoading, error } = useQuery({
  queryKey: computed(() => ['essay-detail', essayId.value, session.value?.accessToken ?? '']),
  queryFn: async (): Promise<EssayDetail> => {
    const id = essayId.value
    const token = session.value?.accessToken
    if (id == null || !token) throw new Error('Unauthorized')
    return await $fetch<EssayDetail>(`${config.public.baseApiURL}/essay/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
  enabled: computed(() => essayId.value != null && status.value === 'authenticated' && !!session.value?.accessToken),
  retry: false,
  refetchInterval: (query) => {
    const data = query.state.data
    if (!data) return false
    const criteries = data.criteries ?? {}
    const hasResults = Object.keys(criteries).length > 0
    return hasResults ? false : 15000
  },
})

const criteriaOrder = (type: string) =>
  type === 'ege'
    ? ['k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7', 'k8', 'k9', 'k10']
    : ['k1', 'k2', 'k3', 'k4', 'k5']

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function scoreLabel(e: EssayDetail) {
  if (e.max_score != null && e.max_score > 0) {
    return `${Math.round(e.total_score)} / ${Math.round(e.max_score)}`
  }
  if (e.total_score_per != null) {
    return `${Math.round(e.total_score_per * 100)}%`
  }
  return '—'
}

const typeLabel = computed(() => {
  if (!essay.value) return ''
  return essay.value.type === 'ege' ? 'Сочинение ЕГЭ' : 'Итоговое сочинение'
})

useHead({
  title: computed(() => (essay.value ? 'Сочинение — Лингво' : 'Сочинение - Лингво')),
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-green-50/30 to-emerald-50/40">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
      <div class="space-y-6">
        <!-- Кнопка назад -->
        <NuxtLink to="/essays" class="inline-flex">
          <Button variant="ghost" size="sm" class="text-gray-600 hover:text-gray-900 -ml-2">
            <ArrowLeft class="mr-2 h-4 w-4" />
            К списку сочинений
          </Button>
        </NuxtLink>

        <!-- Не авторизован -->
        <Card v-if="status === 'unauthenticated'" class="border-green-100/50 bg-white shadow-lg">
          <CardContent class="py-12 text-center text-muted-foreground">
            Войдите в аккаунт, чтобы просматривать сочинение.
          </CardContent>
        </Card>

        <!-- Ошибка (404 / не своё сочинение) -->
        <Card v-else-if="error && !isLoading" class="border-green-100/50 bg-white shadow-lg">
          <CardContent class="py-12 text-center">
            <p class="text-muted-foreground mb-4">Сочинение не найдено или у вас нет доступа к нему.</p>
            <NuxtLink to="/essays">
              <Button variant="outline">К списку сочинений</Button>
            </NuxtLink>
          </CardContent>
        </Card>

        <!-- Загрузка -->
        <template v-else-if="isLoading || !essay">
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <Skeleton class="h-6 w-3/4" />
              <Skeleton class="h-4 w-48 mt-2" />
            </CardHeader>
            <CardContent class="space-y-4">
              <Skeleton class="h-32 w-full" />
              <Skeleton class="h-24 w-full" />
            </CardContent>
          </Card>
        </template>

        <!-- Контент сочинения -->
        <template v-else>
          <!-- Шапка: тема, тип, дата, балл -->
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <span
                  class="inline-flex items-center gap-2 rounded-md px-3 py-1 text-xs font-medium border shrink-0"
                  :class="essay.type === 'ege' ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'"
                >
                  <GraduationCap v-if="essay.type === 'ege'" class="h-4 w-4 shrink-0" />
                  <BookOpen v-else class="h-4 w-4 shrink-0" />
                  {{ typeLabel }}
                </span>
              </div>
              <CardTitle class="text-xl text-gray-800">
                {{ essay.theme }}
              </CardTitle>
              <CardDescription class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm mt-2">
                <span class="flex items-center gap-1.5">
                  <Calendar class="h-4 w-4 shrink-0" />
                  {{ formatDate(essay.ended_at) }}
                </span>
                <span class="font-semibold text-primary">
                  Балл: {{ scoreLabel(essay) }}
                </span>
              </CardDescription>
            </CardHeader>
          </Card>

          <!-- Текст сочинения -->
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2 text-gray-800">
                <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <FileText class="h-4 w-4 text-primary" />
                </div>
                Текст сочинения
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="rounded-lg border border-gray-200 bg-gray-50/50 p-4 text-gray-800 whitespace-pre-wrap leading-relaxed min-h-32">
                {{ essay.text }}
              </div>
            </CardContent>
          </Card>

          <!-- Отчёт по критериям -->
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2 text-gray-800">
                <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <Target class="h-4 w-4 text-primary" />
                </div>
                Отчёт по критериям
              </CardTitle>
              <CardDescription class="text-gray-600">
                Баллы, комментарии и рекомендации по каждому критерию
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div
                v-for="key in criteriaOrder(essay.type)"
                :key="key"
                class="rounded-xl border border-primary/20 bg-primary/5 p-4"
              >
                <div class="flex justify-between items-start gap-3 mb-2">
                  <span class="font-semibold text-gray-800">Критерий {{ key.toUpperCase() }}</span>
                  <span class="text-primary font-semibold shrink-0">
                    {{ (essay.criteries?.[key] as CriterionItem | undefined)?.score ?? '—' }}
                  </span>
                </div>
                <p
                  v-if="(essay.criteries?.[key] as CriterionItem | undefined)?.comment"
                  class="text-sm text-gray-600 leading-relaxed"
                >
                  {{ (essay.criteries?.[key] as CriterionItem)?.comment }}
                </p>
                <ul
                  v-if="Array.isArray((essay.criteries?.[key] as CriterionItem)?.suggestions) && (essay.criteries?.[key] as CriterionItem)?.suggestions?.length"
                  class="mt-2 text-sm text-primary list-disc list-inside space-y-1"
                >
                  <li v-for="(s, i) in (essay.criteries?.[key] as CriterionItem)?.suggestions" :key="i">
                    {{ s }}
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <!-- Действия: новое сочинение / с этой темой -->
          <div class="flex flex-wrap gap-3">
            <NuxtLink to="/essay/new">
              <Button variant="outline" class="border-primary/30 text-primary hover:bg-primary/10">
                <FileEdit class="mr-2 h-4 w-4" />
                Начать новое
              </Button>
            </NuxtLink>
            <NuxtLink :to="{ path: '/essay/new', query: { theme: essay.theme, type: essay.type } }">
              <Button variant="outline" class="border-primary/30 text-primary hover:bg-primary/10">
                <RotateCcw class="mr-2 h-4 w-4" />
                Попробовать с этой темой
              </Button>
            </NuxtLink>
          </div>
        </template>
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
