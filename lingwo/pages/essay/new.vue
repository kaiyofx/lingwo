<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  FileEdit,
  BookOpen,
  GraduationCap,
  Sparkles,
  Shuffle,
  Type,
  Loader2,
  Save,
  Send,
  XCircle,
} from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Label } from '~/components/ui/label'
import { TagsInput, TagsInputInput, TagsInputItem, TagsInputItemDelete, TagsInputItemText } from '~/components/ui/tags-input'
import { toast } from 'vue-sonner'

definePageMeta({
  middleware: 'auth',
})

const config = useRuntimeConfig()
const route = useRoute()
const { status, data: session } = useAuth()
const queryClient = useQueryClient()

onMounted(() => {
  const q = route.query
  if (q.theme && (q.type === 'essay' || q.type === 'ege')) {
    essayType.value = q.type as 'essay' | 'ege'
    themeSource.value = 'own'
    ownThemeText.value = String(q.theme)
  }
})

interface EssayState {
  user_id: string
  type: string
  theme: string
  text: string
  started_at: string
}

interface UserSettings {
  target_percent: number
  auto_save_enabled: boolean
  auto_save_interval_sec: number
}

interface RecommendedTopic {
  theme: string
  level: string
  current_percent: number | null
  target_percent: number
}

const essayType = ref<'essay' | 'ege'>('essay')
const themeSource = ref<'recommended' | 'random' | 'own'>('recommended')
const ownThemeText = ref('')
const randomSections = ref<string[]>([])
const randomTheme = ref('')
const randomLoading = ref(false)
const themeError = ref('')
const { data: activeEssay, isLoading: essayLoading } = useQuery({
  queryKey: computed(() => ['essay-active', session.value?.accessToken ?? '']),
  queryFn: async (): Promise<EssayState | null> => {
    const token = session.value?.accessToken
    if (!token) return null
    try {
      return await $fetch<EssayState>(`${config.public.baseApiURL}/essay`, {
        headers: { Authorization: `Bearer ${token}` },
      })
    } catch {
      return null
    }
  },
  enabled: computed(() => status.value === 'authenticated' && !!session.value?.accessToken),
  retry: false,
})

const { data: settings } = useQuery({
  queryKey: computed(() => ['user-settings', session.value?.accessToken ?? '']),
  queryFn: async (): Promise<UserSettings> => {
    const token = session.value?.accessToken
    if (!token) throw new Error('Unauthorized')
    return await $fetch<UserSettings>(`${config.public.baseApiURL}/settings`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
  enabled: computed(() => !!activeEssay.value && status.value === 'authenticated'),
})

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

const isWritingMode = computed(() => !!activeEssay.value && !essayLoading.value)
const displayTheme = computed(() => {
  if (activeEssay.value) return activeEssay.value.theme
  if (themeSource.value === 'recommended') return recommendedTopic.value?.theme ?? ''
  if (themeSource.value === 'random' && randomTheme.value) return randomTheme.value
  if (themeSource.value === 'own') return ownThemeText.value.trim()
  return ''
})

const levelLabels: Record<string, string> = {
  low: 'Начальный',
  middle: 'Средний',
  high: 'Продвинутый',
}

const levelColors: Record<string, string> = {
  low: 'bg-blue-50 text-blue-700 border-blue-200',
  middle: 'bg-amber-50 text-amber-700 border-amber-200',
  high: 'bg-red-50 text-red-700 border-red-200',
}

const localText = ref('')
watch(
  () => activeEssay.value?.text,
  (t) => {
    if (t !== undefined) localText.value = t
  },
  { immediate: true }
)

let autoSaveTimer: ReturnType<typeof setInterval> | null = null
watch(
  [() => activeEssay.value, () => settings.value, localText],
  ([essay, s], [prevEssay]) => {
    if (autoSaveTimer) {
      clearInterval(autoSaveTimer)
      autoSaveTimer = null
    }
    if (!essay || !s?.auto_save_enabled || essay !== prevEssay) return
    const interval = s.auto_save_interval_sec * 1000
    autoSaveTimer = setInterval(() => {
      if (!localText.value.trim()) return
      const token = session.value?.accessToken
      if (!token) return
      $fetch(`${config.public.baseApiURL}/essay/save`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: { text: localText.value },
      }).catch(() => {})
    }, interval)
    return () => {
      if (autoSaveTimer) clearInterval(autoSaveTimer)
    }
  },
  { immediate: true }
)
onUnmounted(() => {
  if (autoSaveTimer) clearInterval(autoSaveTimer)
})

async function fetchRandomTopic() {
  const token = session.value?.accessToken
  if (!token) return
  randomLoading.value = true
  randomTheme.value = ''
  try {
    const params = new URLSearchParams()
    const parts = randomSections.value.map((s) => s.trim()).filter(Boolean).slice(0, 3)
    if (parts.length) params.set('sections', parts.join('|'))
    const url = `${config.public.baseApiURL}/random_topic${params.toString() ? `?${params.toString()}` : ''}`
    const res = await $fetch<{ theme: string }>(url, { headers: { Authorization: `Bearer ${token}` } })
    randomTheme.value = res.theme
  } catch (e: unknown) {
    toast.error(e && typeof e === 'object' && 'data' in e ? String((e as { data?: { detail?: string } }).data?.detail) : 'Не удалось получить тему')
  } finally {
    randomLoading.value = false
  }
}

const startPending = ref(false)
async function startEssay() {
  const theme = displayTheme.value
  if (!theme.trim()) {
    toast.error('Выберите или введите тему')
    return
  }
  if (themeSource.value === 'own' && !ownThemeText.value.trim()) {
    themeError.value = 'Введите тему'
    toast.error('Введите тему')
    return
  }
  themeError.value = ''

  const token = session.value?.accessToken
  if (!token) return
  startPending.value = true
  try {
    await $fetch(`${config.public.baseApiURL}/essay/start`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: { type: essayType.value, theme, theme_source: themeSource.value },
    })
    await queryClient.invalidateQueries({ queryKey: ['essay-active'] })
    localText.value = ''
  } catch (e: unknown) {
    const msg = e && typeof e === 'object' && 'data' in e ? (e as { data?: { detail?: string } }).data?.detail : null
    const errMsg = typeof msg === 'string' ? msg : 'Не удалось начать сочинение'
    themeError.value = themeSource.value === 'own' ? errMsg : ''
    toast.error(errMsg)
  } finally {
    startPending.value = false
  }
}

const savePending = ref(false)
async function saveEssay() {
  const token = session.value?.accessToken
  if (!token || !activeEssay.value) return
  if (!localText.value.trim()) {
    toast.error('Введите текст')
    return
  }
  savePending.value = true
  try {
    await $fetch(`${config.public.baseApiURL}/essay/save`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: { text: localText.value },
    })
    toast.success('Сохранено')
  } catch {
    toast.error('Не удалось сохранить')
  } finally {
    savePending.value = false
  }
}

const submitPending = ref(false)
async function submitEssay() {
  const token = session.value?.accessToken
  if (!token || !activeEssay.value) return
  if (!localText.value.trim()) {
    toast.error('Введите текст сочинения')
    return
  }
  submitPending.value = true
  try {
    const res = await $fetch<{ id: number }>(`${config.public.baseApiURL}/essay/end`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: { text: localText.value },
    })
    await queryClient.invalidateQueries({ queryKey: ['essay-active'] })
    await queryClient.invalidateQueries({ queryKey: ['essays-list'] })
    navigateTo(`/essays/${res.id}`)
    toast.success('Сочинение отправлено на проверку')
  } catch (e: unknown) {
    const msg = e && typeof e === 'object' && 'data' in e ? (e as { data?: { detail?: string } }).data?.detail : null
    toast.error(typeof msg === 'string' ? msg : 'Не удалось отправить')
  } finally {
    submitPending.value = false
  }
}

const clearPending = ref(false)
async function clearEssay() {
  const token = session.value?.accessToken
  if (!token) return
  clearPending.value = true
  try {
    await $fetch(`${config.public.baseApiURL}/essay/clear`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    await queryClient.invalidateQueries({ queryKey: ['essay-active'] })
    localText.value = ''
  } catch {
    toast.error('Не удалось завершить')
  } finally {
    clearPending.value = false
  }
}

useHead({
  title: isWritingMode.value ? 'Новое сочинение — Лингво' : 'Выбор темы — Лингво',
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-green-50/30 to-emerald-50/40">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
      <div class="space-y-6">
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <FileEdit class="h-4 w-4 text-primary" />
              </div>
              {{ isWritingMode ? 'Новое сочинение' : 'Выбор темы и типа' }}
            </CardTitle>
            <CardDescription class="text-gray-600">
              {{ isWritingMode ? 'Пишите сочинение. Сохранение можно отправить на проверку или завершить без результатов.' : 'Выберите тип работы и способ задания темы.' }}
            </CardDescription>
          </CardHeader>
        </Card>

        <template v-if="status === 'unauthenticated'">
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardContent class="py-12 text-center text-muted-foreground">
              Войдите в аккаунт, чтобы начать сочинение.
            </CardContent>
          </Card>
        </template>

        <!-- Режим написания: textarea + кнопки -->
        <template v-else-if="isWritingMode && activeEssay">
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader class="pb-2">
              <div class="flex flex-wrap items-center gap-2 mb-1.5">
                <span
                  class="inline-flex items-center gap-2 rounded-md px-3 py-1 text-xs font-medium border shrink-0"
                  :class="activeEssay.type === 'ege' ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-emerald-50 text-emerald-800 border-emerald-200'"
                >
                  <GraduationCap v-if="activeEssay.type === 'ege'" class="h-4 w-4 shrink-0" />
                  <BookOpen v-else class="h-4 w-4 shrink-0" />
                  {{ activeEssay.type === 'ege' ? 'ЕГЭ' : 'Итоговое сочинение' }}
                </span>
              </div>
              <CardTitle class="text-base font-semibold text-gray-800">
                {{ activeEssay.theme }}
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-2">
                <Label for="essay-text" class="text-sm font-medium text-gray-700">Текст сочинения</Label>
                <textarea
                  id="essay-text"
                  v-model="localText"
                  placeholder="Введите текст сочинения..."
                  class="flex min-h-[280px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                />
              </div>
              <div class="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  class="bg-primary text-white hover:bg-primary/90"
                  :disabled="savePending || !localText.trim()"
                  @click="saveEssay"
                >
                  <Save class="mr-2 h-4 w-4" />
                  Сохранить
                </Button>
                <Button
                  size="sm"
                  class="bg-primary text-white hover:bg-primary/90"
                  :disabled="submitPending || !localText.trim()"
                  @click="submitEssay"
                >
                  <Send class="mr-2 h-4 w-4" />
                  Отправить на проверку
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  class="border-red-200 text-red-600 hover:bg-red-50"
                  :disabled="clearPending"
                  @click="clearEssay"
                >
                  <XCircle class="mr-2 h-4 w-4" />
                  Завершить без результатов
                </Button>
              </div>
            </CardContent>
          </Card>
        </template>

        <!-- Режим выбора темы -->
        <template v-else-if="!essayLoading">
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <CardTitle class="text-base text-gray-800">Тип сочинения</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="flex flex-wrap gap-3">
                <button
                  type="button"
                  class="flex items-center gap-2 rounded-lg border px-4 py-3 text-sm font-medium transition-colors"
                  :class="essayType === 'essay' ? 'border-primary bg-primary/10 text-primary' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                  @click="essayType = 'essay'"
                >
                  <BookOpen class="h-4 w-4" />
                  Итоговое сочинение
                </button>
                <button
                  type="button"
                  class="flex items-center gap-2 rounded-lg border px-4 py-3 text-sm font-medium transition-colors"
                  :class="essayType === 'ege' ? 'border-primary bg-primary/10 text-primary' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'"
                  @click="essayType = 'ege'"
                >
                  <GraduationCap class="h-4 w-4" />
                  ЕГЭ
                </button>
              </div>
            </CardContent>
          </Card>

          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardHeader>
              <CardTitle class="text-base text-gray-800">Тема</CardTitle>
              <CardDescription class="text-gray-600">Рекомендуемая, случайная или своя</CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex flex-col gap-3">
                <div
                  class="rounded-lg border p-3 cursor-pointer transition-colors hover:bg-primary/5"
                  :class="themeSource === 'recommended' ? 'border-primary bg-primary/5' : 'border-gray-200'"
                  @click="themeSource = 'recommended'"
                >
                  <label class="flex items-center gap-3 cursor-pointer">
                    <input v-model="themeSource" type="radio" value="recommended" class="sr-only" />
                    <Sparkles class="h-4 w-4 text-primary shrink-0" />
                    <span class="font-medium">Рекомендуемая тема</span>
                    <span
                      v-if="recommendedTopic?.level"
                      class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border"
                      :class="levelColors[recommendedTopic.level] ?? 'bg-gray-50 text-gray-600 border-gray-200'"
                    >
                      {{ levelLabels[recommendedTopic.level] ?? recommendedTopic.level }}
                    </span>
                  </label>
                  <div class="ml-7 mt-2">
                    <Loader2 v-if="recommendedLoading" class="h-4 w-4 animate-spin text-muted-foreground" />
                    <p v-else-if="recommendedTopic?.theme" class="text-sm text-primary font-medium">
                      {{ recommendedTopic.theme }}
                    </p>
                    <p v-else class="text-sm text-muted-foreground">
                      Напишите хотя бы одно сочинение, чтобы получить персональную рекомендацию
                    </p>
                    <p
                      v-if="recommendedTopic?.current_percent != null"
                      class="text-xs text-muted-foreground mt-1"
                    >
                      Ваш текущий уровень: {{ recommendedTopic.current_percent }}% · Цель: {{ recommendedTopic.target_percent }}%
                    </p>
                  </div>
                </div>

                <div class="rounded-lg border p-3" :class="themeSource === 'random' ? 'border-primary bg-primary/5' : 'border-gray-200'">
                  <label class="flex items-center gap-3 cursor-pointer mb-2">
                    <input v-model="themeSource" type="radio" value="random" class="sr-only" />
                    <Shuffle class="h-4 w-4 text-primary shrink-0" />
                    <span class="font-medium">Случайная тема</span>
                  </label>
                  <div class="ml-7 space-y-2">
                    <TagsInput
                      v-model="randomSections"
                      class="w-full min-h-9"
                      @invalid="(msg) => toast.error(msg)"
                    >
                      <TagsInputItem v-for="(item, index) in randomSections" :key="index" :value="item">
                        <TagsInputItemText />
                        <TagsInputItemDelete />
                      </TagsInputItem>
                      <TagsInputInput placeholder="Ввод разделов. Enter - добавить (до 3)" />
                    </TagsInput>
                    <Button size="sm" variant="outline" :disabled="randomLoading" @click="fetchRandomTopic">
                      <Loader2 v-if="randomLoading" class="mr-2 h-4 w-4 animate-spin" />
                      Получить случайную тему
                    </Button>
                    <p v-if="randomTheme" class="text-sm text-primary font-medium mt-2">{{ randomTheme }}</p>
                  </div>
                </div>

                <div class="rounded-lg border p-3" :class="themeSource === 'own' ? 'border-primary bg-primary/5' : 'border-gray-200'">
                  <label class="flex items-center gap-3 cursor-pointer mb-2">
                    <input v-model="themeSource" type="radio" value="own" class="sr-only" />
                    <Type class="h-4 w-4 text-primary shrink-0" />
                    <span class="font-medium">Своя тема</span>
                  </label>
                  <div class="ml-7 space-y-2">
                    <input
                      v-model="ownThemeText"
                      type="text"
                      placeholder="Введите тему сочинения"
                      class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                    />
                    <p v-if="themeError" class="text-sm text-red-600">{{ themeError }}</p>
                  </div>
                </div>
              </div>

              <Button
                class="w-full sm:w-auto"
                :disabled="startPending || !displayTheme.trim()"
                @click="startEssay"
              >
                <Loader2 v-if="startPending" class="mr-2 h-4 w-4 animate-spin" />
                Начать сочинение
              </Button>
            </CardContent>
          </Card>
        </template>

        <template v-else>
          <Card class="border-green-100/50 bg-white shadow-lg">
            <CardContent class="py-12 text-center text-muted-foreground">
              Загрузка...
            </CardContent>
          </Card>
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
