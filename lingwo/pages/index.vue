<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { FileEdit, TrendingUp, Award, Calendar, Lightbulb, Target, BookOpen, GraduationCap, Sparkles } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Skeleton } from '~/components/ui/skeleton'
import { CurveType } from '@unovis/ts'
import { VisAxis, VisLine, VisXYContainer, VisGroupedBar } from '@unovis/vue'
import {
  ChartContainer,
  ChartCrosshair,
  ChartTooltip,
  ChartTooltipContent,
  componentToString,
  type ChartConfig,
} from '~/components/ui/chart'

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
}

const { status, data: session } = useAuth()
const config = useRuntimeConfig()

const { data: essaysRaw, isLoading: essaysLoading } = useQuery({
  queryKey: computed(() => ['essays', session.value?.accessToken ?? '']),
  queryFn: async (): Promise<EssayListItem[]> => {
    const token = session.value?.accessToken
    if (!token) return []
    return await $fetch<EssayListItem[]>(`${config.public.baseApiURL}/essays`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
  enabled: computed(() => status.value === 'authenticated' && !!session.value?.accessToken),
})

const essays = computed(() => essaysRaw.value ?? [])

interface RecommendedTopic {
  theme: string
  level: string
  current_percent: number | null
  target_percent: number
}

const { data: recommendedTopic, isLoading: recommendedLoading } = useQuery({
  queryKey: computed(() => ['recommended-topic', session.value?.accessToken ?? '']),
  queryFn: async (): Promise<RecommendedTopic | null> => {
    const token = session.value?.accessToken
    if (!token) return null
    return await $fetch<RecommendedTopic>(`${config.public.baseApiURL}/recommended_topic`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
  enabled: computed(() => status.value === 'authenticated' && !!session.value?.accessToken),
  staleTime: 1000 * 60 * 60,
})

const levelLabels: Record<string, string> = {
  low: 'Начальный',
  middle: 'Средний',
  high: 'Продвинутый',
}

const levelColors: Record<string, string> = {
  low: 'text-blue-700 bg-blue-50 border-blue-200',
  middle: 'text-amber-700 bg-amber-50 border-amber-200',
  high: 'text-red-700 bg-red-50 border-red-200',
}

// Оценённые работы (есть total_score_per)
const evaluatedEssays = computed(() =>
  essays.value.filter((e) => e.total_score_per != null)
)

// Разделение по типу: итоговое сочинение (essay) и ЕГЭ (ege)
const essaysByType = computed(() => {
  const essay = evaluatedEssays.value.filter((e) => e.type === 'essay')
  const ege = evaluatedEssays.value.filter((e) => e.type === 'ege')
  return { essay, ege }
})

function avgPercent(items: { total_score_per: number | null }[]): number | null {
  const withPer = items.filter((e) => e.total_score_per != null) as { total_score_per: number }[]
  if (withPer.length === 0) return null
  const sum = withPer.reduce((a, e) => a + e.total_score_per, 0)
  return Math.round((sum / withPer.length) * 100)
}

function bestPercent(items: { total_score_per: number | null }[]): number | null {
  const withPer = items.filter((e) => e.total_score_per != null) as { total_score_per: number }[]
  if (withPer.length === 0) return null
  return Math.round(Math.max(...withPer.map((e) => e.total_score_per)) * 100)
}

const metrics = computed(() => {
  const total = essays.value.length
  const avg = avgPercent(evaluatedEssays.value)
  const best = bestPercent(evaluatedEssays.value)
  return {
    totalEssays: total,
    averageScorePer: avg,
    bestScorePer: best,
    daysStreak: 0, // не считаем из API
  }
})

const metricsEssay = computed(() => ({
  total: essaysByType.value.essay.length,
  averageScorePer: avgPercent(essaysByType.value.essay),
  bestScorePer: bestPercent(essaysByType.value.essay),
}))

const metricsEge = computed(() => ({
  total: essaysByType.value.ege.length,
  averageScorePer: avgPercent(essaysByType.value.ege),
  bestScorePer: bestPercent(essaysByType.value.ege),
}))

// Данные для графика прогресса: последние 6 оценённых работ (процент)
const progressData = computed(() => {
  const list = evaluatedEssays.value.slice(0, 6).reverse()
  return list.map((e) => {
    const d = new Date(e.ended_at)
    const dateStr = `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}`
    const per = e.total_score_per != null ? Math.round(e.total_score_per * 100) : 0
    return { date: dateStr, score: per, type: e.type }
  })
})

type ProgressData = { date: string; score: number; type: string }

const progressChartConfig = {
  score: {
    label: 'Процент',
    color: '#6DCE78',
  },
} satisfies ChartConfig

// Переключатель: Итоговое сочинение (k1–k5) или ЕГЭ (K1–K10)
const criteriaTab = ref<'essay' | 'ege'>('essay')

const ESSAY_CRITERIA_KEYS = ['k1', 'k2', 'k3', 'k4', 'k5']
const EGE_CRITERIA_KEYS = ['k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7', 'k8', 'k9', 'k10']
// Максимальный балл по каждому критерию ЕГЭ (для перевода в долю 0–1)
const EGE_MAX_BY_CRITERION: Record<string, number> = { k1: 1, k2: 3, k3: 2, k4: 1, k5: 2, k6: 1, k7: 3, k8: 3, k9: 3, k10: 3 }

// Средний процент (0–1) по каждому критерию: балл / макс. балл по критерию, затем среднее по работам
const criteriaData = computed(() => {
  const type = criteriaTab.value
  const keys = type === 'essay' ? ESSAY_CRITERIA_KEYS : EGE_CRITERIA_KEYS
  const maxByKey = type === 'essay' ? undefined : EGE_MAX_BY_CRITERION
  const list = evaluatedEssays.value.filter((e) => e.type === type && e.criteries && Object.keys(e.criteries).length > 0)
  if (list.length === 0) {
    return keys.map((c) => ({ criterion: c, score: 0 }))
  }
  return keys.map((key) => {
    let sumPer = 0
    let count = 0
    const maxScore = type === 'essay' ? 1 : (maxByKey?.[key] ?? 1)
    for (const essay of list) {
      const c = essay.criteries?.[key]
      if (c != null && typeof c === 'object' && typeof (c as CriterionItem).score === 'number') {
        const raw = (c as CriterionItem).score
        sumPer += maxScore > 0 ? raw / maxScore : 0
        count += 1
      }
    }
    const score = count > 0 ? Math.round((sumPer / count) * 100) / 100 : 0
    return { criterion: key, score }
  })
})

type CriteriaData = { criterion: string; score: number }

const criteriaChartConfig = computed(() => ({
  score: {
    label: 'Доля выполнения (0–1)',
    color: '#6DCE78',
  },
}))

const criteriaYDomain = [0, 1] as const

// Рекомендации из последнего по дате сочинения: комментарии и советы по критериям + тип работы
const recommendations = computed(() => {
  const withCrit = evaluatedEssays.value
    .filter((e) => e.criteries && Object.keys(e.criteries).length > 0)
    .sort((a, b) => new Date(b.ended_at).getTime() - new Date(a.ended_at).getTime())
  const last = withCrit[0]
  if (!last?.criteries) return { type: null as string | null, typeLabel: '', theme: '', items: [] as { title: string; description: string; improvement: string }[] }
  const out: { title: string; description: string; improvement: string }[] = []
  const keys = Object.keys(last.criteries).sort()
  for (const key of keys) {
    const c = last.criteries[key] as CriterionItem | undefined
    if (!c || typeof c !== 'object') continue
    const comment = typeof c.comment === 'string' ? c.comment.trim() : ''
    if (!comment) continue
    const suggestions = Array.isArray(c.suggestions) ? c.suggestions.filter((s): s is string => typeof s === 'string') : []
    const improvement = suggestions.length > 0 ? suggestions.join('. ') : ''
    out.push({
      title: `Критерий ${key.toUpperCase()}`,
      description: comment,
      improvement,
    })
  }
  const type = last.type === 'ege' ? 'ege' : 'essay'
  const typeLabel = type === 'ege' ? 'Сочинение ЕГЭ' : 'Итоговое сочинение'
  const theme = typeof last.theme === 'string' ? last.theme.trim() : ''
  return { type, typeLabel, theme, items: out }
})

const motivationalPhrase = computed(() => {
  const m = metrics.value
  if (m.averageScorePer != null && m.averageScorePer >= 80) {
    return `Ваш средний процент выполнения ${m.averageScorePer}% — отличный результат!`
  }
  if (m.totalEssays === 0) {
    return 'Начните первое сочинение — статистика появится после проверки работ.'
  }
  return 'Продолжайте в том же духе! Каждая тренировка приближает вас к цели.'
})

useHead({
  title: 'Лингво - Главная',
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-green-50/30 to-emerald-50/40">
    <div class="container mx-auto px-4 py-8">
      <!-- Для неавторизованных пользователей -->
      <div v-if="status !== 'authenticated'" class="max-w-4xl mx-auto">
        <header class="text-center mb-16">
          <div class="inline-flex items-center justify-center w-full mb-4">
            <NuxtImg width="200" src="/assets/logo.svg" alt="Lingwo"/>
          </div>
          <h1 class="text-5xl font-bold text-gray-800 mb-4">Добро пожаловать в Лингво</h1>
          <p class="text-xl text-gray-600 mb-2">Изучайте языки легко и эффективно</p>
          <NuxtLink to="/about" class="text-sm text-primary hover:text-primary/80 font-medium transition-colors">
            О проекте
          </NuxtLink>
        </header>

        <div class="grid md:grid-cols-2 gap-6 mb-16">
          <NuxtLink 
            to="/login" 
            class="group bg-white rounded-xl shadow-lg border border-green-100/50 p-8 hover:shadow-xl transition-all hover:scale-105"
          >
            <div class="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary to-emerald-400 mb-4 mx-auto group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-gray-800 text-center mb-2">Вход</h3>
            <p class="text-gray-600 text-center">Войдите в свой аккаунт</p>
          </NuxtLink>

          <NuxtLink 
            to="/register" 
            class="group bg-white rounded-xl shadow-lg border border-green-100/50 p-8 hover:shadow-xl transition-all hover:scale-105"
          >
            <div class="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-emerald-400 to-primary mb-4 mx-auto group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <h3 class="text-2xl font-bold text-gray-800 text-center mb-2">Регистрация</h3>
            <p class="text-gray-600 text-center">Создайте новый аккаунт</p>
          </NuxtLink>
        </div>

        <!-- Features Section -->
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="bg-white/80 backdrop-blur rounded-lg p-6 border border-green-100/50">
            <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
            </div>
            <h4 class="text-lg font-semibold text-gray-800 mb-2">Множество языков</h4>
            <p class="text-sm text-gray-600">Изучайте языки со всего мира</p>
          </div>

          <div class="bg-white/80 backdrop-blur rounded-lg p-6 border border-green-100/50">
            <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 class="text-lg font-semibold text-gray-800 mb-2">Эффективное обучение</h4>
            <p class="text-sm text-gray-600">Проверенные методики и подходы</p>
          </div>

          <div class="bg-white/80 backdrop-blur rounded-lg p-6 border border-green-100/50 sm:col-span-2 lg:col-span-1">
            <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 class="text-lg font-semibold text-gray-800 mb-2">Учитесь в своем темпе</h4>
            <p class="text-sm text-gray-600">Гибкий график и персональный подход</p>
          </div>
        </div>
      </div>

      <!-- Дашборд для авторизованных пользователей -->
      <div v-else class="space-y-6">
        <!-- Верхний блок: Приветствие и кнопка -->
        <Card class="bg-gradient-to-r from-primary/10 to-emerald-50/50 border-primary/20">
          <CardHeader>
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <CardTitle class="text-3xl mb-2">
                  Добро пожаловать, {{ session?.user?.name || 'Пользователь' }}!
                </CardTitle>
                <CardDescription class="text-base">
                  {{ motivationalPhrase }}
                </CardDescription>
              </div>
              <NuxtLink to="/essay/new">
                <Button size="lg" class="w-full md:w-auto">
                  <FileEdit class="mr-2 h-5 w-5" />
                  Начать новое сочинение
                </Button>
              </NuxtLink>
            </div>
          </CardHeader>
        </Card>

        <!-- Рекомендуемая тема дня -->
        <Card class="border-primary/20 bg-gradient-to-r from-primary/5 to-emerald-50/30">
          <CardHeader class="pb-3">
            <CardTitle class="flex items-center gap-2 text-lg">
              <Sparkles class="h-5 w-5 text-primary" />
              Тема дня
            </CardTitle>
            <CardDescription>Персональная рекомендация на основе вашего прогресса</CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="recommendedLoading" class="space-y-2">
              <Skeleton class="h-5 w-3/4" />
              <Skeleton class="h-4 w-1/3" />
            </div>
            <div v-else-if="recommendedTopic?.theme">
              <p class="text-base font-semibold text-gray-800 mb-2">{{ recommendedTopic.theme }}</p>
              <div class="flex flex-wrap items-center gap-2">
                <span
                  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border"
                  :class="levelColors[recommendedTopic.level] ?? 'text-gray-600 bg-gray-50 border-gray-200'"
                >
                  {{ levelLabels[recommendedTopic.level] ?? recommendedTopic.level }}
                </span>
                <span v-if="recommendedTopic.current_percent != null" class="text-xs text-muted-foreground">
                  Уровень: {{ recommendedTopic.current_percent }}% · Цель: {{ recommendedTopic.target_percent }}%
                </span>
              </div>
              <NuxtLink
                :to="{ path: '/essay/new', query: { theme: recommendedTopic.theme, type: 'essay' } }"
                class="mt-3 inline-block"
              >
                <Button size="sm" variant="outline" class="border-primary/30 text-primary hover:bg-primary/10">
                  <FileEdit class="mr-2 h-4 w-4" />
                  Написать на эту тему
                </Button>
              </NuxtLink>
            </div>
            <p v-else class="text-sm text-muted-foreground">
              Напишите первое сочинение, чтобы получить персональную рекомендацию.
            </p>
          </CardContent>
        </Card>

        <!-- Ключевые метрики (общие) -->
        <div v-if="essaysLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card v-for="i in 4" :key="i">
            <CardHeader class="pb-2">
              <Skeleton class="h-4 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton class="h-8 w-16" />
            </CardContent>
          </Card>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium">Всего сочинений</CardTitle>
              <FileEdit class="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">{{ metrics.totalEssays }}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium">Средний процент</CardTitle>
              <TrendingUp class="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">
                {{ metrics.averageScorePer != null ? metrics.averageScorePer + '%' : '—' }}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium">Лучший процент</CardTitle>
              <Award class="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">
                {{ metrics.bestScorePer != null ? metrics.bestScorePer + '%' : '—' }}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium">Оценённых работ</CardTitle>
              <Calendar class="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">{{ evaluatedEssays.length }}</div>
            </CardContent>
          </Card>
        </div>

        <!-- Разделение: Итоговое сочинение и ЕГЭ -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card class="border-emerald-200 bg-emerald-50/30">
            <CardHeader>
              <CardTitle class="flex items-center gap-2 text-emerald-800">
                <BookOpen class="h-5 w-5" />
                Итоговое сочинение
              </CardTitle>
              <CardDescription>Работы вида "Итоговое сочинение"</CardDescription>
            </CardHeader>
            <CardContent class="space-y-3">
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Количество</span>
                <span class="font-medium">{{ metricsEssay.total }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Средний процент</span>
                <span class="font-medium">
                  {{ metricsEssay.averageScorePer != null ? metricsEssay.averageScorePer + '%' : '—' }}
                </span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Лучший процент</span>
                <span class="font-medium">
                  {{ metricsEssay.bestScorePer != null ? metricsEssay.bestScorePer + '%' : '—' }}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card class="border-amber-200 bg-amber-50/30">
            <CardHeader>
              <CardTitle class="flex items-center gap-2 text-amber-800">
                <GraduationCap class="h-5 w-5" />
                Сочинение ЕГЭ (задание 27)
              </CardTitle>
              <CardDescription>Работы вида "Сочинение ЕГЭ"</CardDescription>
            </CardHeader>
            <CardContent class="space-y-3">
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Количество</span>
                <span class="font-medium">{{ metricsEge.total }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Средний процент</span>
                <span class="font-medium">
                  {{ metricsEge.averageScorePer != null ? metricsEge.averageScorePer + '%' : '—' }}
                </span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Лучший процент</span>
                <span class="font-medium">
                  {{ metricsEge.bestScorePer != null ? metricsEge.bestScorePer + '%' : '—' }}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Графики и анализ -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Динамика прогресса -->
          <Card>
            <CardHeader>
              <CardTitle>Динамика прогресса</CardTitle>
              <CardDescription>Процент выполнения по датам (последние 6 оценённых работ)</CardDescription>
            </CardHeader>
            <CardContent>
              <ChartContainer v-if="progressData.length" :config="progressChartConfig" class="h-[300px]">
                <VisXYContainer
                  :data="progressData"
                  :margin="{ left: 20, bottom: 40, right: 20 }"
                  :y-domain="[0, 100]"
                >
                  <VisLine
                    :x="(d: ProgressData, i: number) => i"
                    :y="(d: ProgressData) => d.score"
                    :color="progressChartConfig.score.color"
                    :curve-type="CurveType.MonotoneX"
                    :line-width="3"
                  />
                  <VisAxis
                    type="x"
                    :tick-line="false"
                    :domain-line="false"
                    :grid-line="false"
                    :num-ticks="progressData.length"
                    :tick-format="(v: number) => progressData[v]?.date || ''"
                    :tick-values="progressData.map((_, i) => i)"
                  />
                  <VisAxis
                    type="y"
                    :num-ticks="5"
                    :tick-line="false"
                    :domain-line="false"
                    :grid-line="true"
                  />
                  <ChartTooltip />
                  <ChartCrosshair
                    :template="componentToString(progressChartConfig, ChartTooltipContent, { 
                      labelFormatter: (d: number | Date) => {
                        const index = typeof d === 'number' ? Math.round(d) : 0
                        return progressData[index]?.date || ''
                      }
                    })"
                    :color="progressChartConfig.score.color"
                  />
                </VisXYContainer>
              </ChartContainer>
              <p v-else class="text-sm text-muted-foreground py-8 text-center">
                Нет данных для графика. После проверки сочинений здесь появится динамика процента.
              </p>
            </CardContent>
          </Card>

          <!-- Оценки по критериям (ИС или ЕГЭ) -->
          <Card>
            <CardHeader>
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <CardTitle>Оценки по критериям</CardTitle>
                  <CardDescription>Средний балл по критериям за выбранный тип работ</CardDescription>
                </div>
                <div class="flex rounded-lg border border-input bg-muted p-1">
                  <button
                    type="button"
                    class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
                    :class="criteriaTab === 'essay' ? 'bg-background text-foreground shadow' : 'text-muted-foreground hover:text-foreground'"
                    @click="criteriaTab = 'essay'"
                  >
                    Итоговое сочинение
                  </button>
                  <button
                    type="button"
                    class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
                    :class="criteriaTab === 'ege' ? 'bg-background text-foreground shadow' : 'text-muted-foreground hover:text-foreground'"
                    @click="criteriaTab = 'ege'"
                  >
                    ЕГЭ
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ChartContainer :config="criteriaChartConfig" class="h-[300px]">
                <VisXYContainer
                  :data="criteriaData"
                  :margin="{ left: -24, bottom: 40, right: 20 }"
                  :y-domain="criteriaYDomain"
                >
                  <VisGroupedBar
                    :x="(d: CriteriaData, i: number) => i"
                    :y="(d: CriteriaData) => d.score"
                    :color="criteriaChartConfig.score.color"
                    :rounded-corners="10"
                  />
                  <VisAxis
                    type="x"
                    :tick-line="false"
                    :domain-line="false"
                    :grid-line="false"
                    :num-ticks="criteriaData.length"
                    :tick-format="(v: number) => criteriaData[v]?.criterion || ''"
                    :tick-values="criteriaData.map((_, i) => i)"
                  />
                  <VisAxis
                    type="y"
                    :num-ticks="5"
                    :tick-line="false"
                    :domain-line="false"
                    :grid-line="true"
                  />
                  <ChartTooltip />
                  <ChartCrosshair
                    :template="componentToString(criteriaChartConfig, ChartTooltipContent, { 
                      labelFormatter: (d: number | Date) => {
                        const index = typeof d === 'number' ? Math.round(d) : 0
                        return criteriaData[index]?.criterion || ''
                      }
                    })"
                    color="#0000"
                  />
                </VisXYContainer>
              </ChartContainer>
              <p v-if="criteriaData.every((d) => d.score === 0)" class="text-sm text-muted-foreground mt-4 text-center">
                {{ criteriaTab === 'essay' ? 'Нет оценённых итоговых сочинений с критериями.' : 'Нет оценённых сочинений ЕГЭ с критериями.' }}
              </p>
            </CardContent>
          </Card>
        </div>

        <!-- Рекомендации -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Lightbulb class="h-5 w-5 text-primary" />
              Интеллектуальные рекомендации
            </CardTitle>
            <CardDescription>Персональные советы на основе анализа ваших работ</CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="recommendations.items.length" class="space-y-4">
              <p class="text-sm font-medium text-muted-foreground pb-2 border-b border-primary/20">
                К последней работе: <span class="text-primary font-semibold">{{ recommendations.theme }} ({{ recommendations.typeLabel }})</span>
              </p>
              <div
                v-for="(rec, index) in recommendations.items"
                :key="index"
                class="p-4 rounded-lg border border-primary/20 bg-primary/5"
              >
                <div class="flex items-start gap-3">
                  <Target class="h-5 w-5 text-primary mt-0.5 shrink-0" />
                  <div class="flex-1">
                    <h4 class="font-semibold text-lg mb-1">{{ rec.title }}</h4>
                    <p class="text-sm text-muted-foreground mb-2">{{ rec.description }}</p>
                    <p v-if="rec.improvement" class="text-sm font-medium text-primary">{{ rec.improvement }}</p>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="text-sm text-muted-foreground py-6 text-center">
              Рекомендации появятся после проверки сочинения — здесь будут комментарии и советы по каждому критерию из последней работы.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Smooth transitions */
* {
  transition-property: transform, box-shadow, background-color;
  transition-duration: 0.3s;
  transition-timing-function: ease-in-out;
}
</style>
