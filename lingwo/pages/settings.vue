<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { Settings, Download, Save, Target, FileText } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Checkbox } from '~/components/ui/checkbox'
import { Slider } from '~/components/ui/slider'
import { Label } from '~/components/ui/label'
import { toast } from 'vue-sonner'

useHead({
  title: 'Настройки - Лингво'
})

const config = useRuntimeConfig()
const { status, data: session } = useAuth()
const queryClient = useQueryClient()

interface UserSettings {
  target_percent: number
  auto_save_enabled: boolean
  auto_save_interval_sec: number
}

const { data: settingsRaw } = useQuery({
  queryKey: computed(() => ['user-settings', session.value?.accessToken ?? '']),
  queryFn: async (): Promise<UserSettings> => {
    const token = session.value?.accessToken
    if (!token) throw new Error('Unauthorized')
    return await $fetch<UserSettings>(`${config.public.baseApiURL}/settings`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  },
  enabled: computed(() => status.value === 'authenticated' && !!session.value?.accessToken),
})

// Настройка целей: целевой процент 0–100
const targetPercent = ref([70])
// Настройки автосохранения
const autoSaveEnabled = ref(true)
const autoSaveInterval = ref([30])

watch(settingsRaw, (v) => {
  if (v) {
    targetPercent.value = [v.target_percent]
    autoSaveEnabled.value = v.auto_save_enabled
    autoSaveInterval.value = [v.auto_save_interval_sec]
  }
}, { immediate: true })

const exportStatistics = () => {
  toast.success('Статистика экспортирована в CSV')
}

const savePending = ref(false)
const saveSettings = async () => {
  const token = session.value?.accessToken
  if (!token) {
    toast.error('Войдите в аккаунт')
    return
  }
  savePending.value = true
  const newData: UserSettings = {
    target_percent: targetPercent.value[0],
    auto_save_enabled: autoSaveEnabled.value,
    auto_save_interval_sec: autoSaveInterval.value[0],
  }
  try {
    await $fetch(`${config.public.baseApiURL}/settings`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
      body: newData,
    })
    queryClient.setQueryData(['user-settings', token], newData)
    toast.success('Настройки сохранены')
  } catch (e: unknown) {
    toast.error(e && typeof e === 'object' && 'data' in e ? String((e as { data?: { detail?: string } }).data?.detail) : 'Не удалось сохранить')
  } finally {
    savePending.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-green-50/30 to-emerald-50/40">
    <div class="container mx-auto px-4 py-8 max-w-4xl">

      <div class="space-y-6">
        <!-- Настройка целей -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Target class="h-4 w-4 text-primary" />
              </div>
              Настройка целей
            </CardTitle>
            <CardDescription class="text-gray-600">
              Установите цели для эффективного обучения
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-6">
            <!-- Целевой процент -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <Label for="target-percent" class="text-sm font-medium text-gray-700">
                  Целевой процент
                </Label>
                <span class="text-lg font-semibold text-primary">
                  {{ targetPercent[0] }}%
                </span>
              </div>
              <Slider
                id="target-percent"
                v-model="targetPercent"
                :min="0"
                :max="100"
                :step="5"
                class="w-full"
              />
              <div class="flex justify-between text-xs text-muted-foreground">
                <span>0%</span>
                <span>100%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Настройки автосохранения -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Save class="h-4 w-4 text-primary" />
              </div>
              Настройки автосохранения
            </CardTitle>
            <CardDescription class="text-gray-600">
              Управляйте автоматическим сохранением ваших работ
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center gap-4 rounded-lg border border-transparent p-3 transition-colors hover:bg-primary/5 hover:border-primary/10">
              <Checkbox 
                id="auto-save" 
                v-model="autoSaveEnabled"
                class="shrink-0 border-primary data-[state=checked]:bg-primary data-[state=checked]:border-primary"
              />
              <Label 
                for="auto-save" 
                class="flex-1 cursor-pointer text-base font-medium text-gray-800"
              >
                Включить автосохранение
              </Label>
            </div>

            <div v-if="autoSaveEnabled" class="space-y-4 rounded-lg bg-primary/5 border border-primary/10 p-4">
              <div class="flex items-center justify-between mb-2">
                <Label for="save-interval" class="text-sm font-medium text-gray-700">
                  Интервал автосохранения (секунды)
                </Label>
                <span class="text-sm font-semibold text-primary">
                  {{ autoSaveInterval[0] }} сек
                </span>
              </div>
              <div class="py-2">
                <Slider
                  id="save-interval"
                  v-model="autoSaveInterval"
                  :min="10"
                  :max="120"
                  :step="10"
                  class="w-full"
                />
              </div>
              <div class="flex justify-between text-xs text-muted-foreground mt-2">
                <span>10 сек</span>
                <span>120 сек</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Экспорт статистики -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <FileText class="h-4 w-4 text-primary" />
              </div>
              Экспорт данных
            </CardTitle>
            <CardDescription class="text-gray-600">
              Скачайте вашу статистику для анализа
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              @click="exportStatistics"
              variant="outline"
              size="lg"
              class="w-full md:w-auto border-primary/30 text-primary hover:bg-primary/10 hover:border-primary"
            >
              <Download class="mr-2 h-5 w-5" />
              Экспортировать статистику (CSV)
            </Button>
          </CardContent>
        </Card>

        <!-- Кнопка сохранения -->
        <div class="flex justify-end gap-4 pt-4">
          <Button 
            @click="saveSettings"
            size="lg"
            class="min-w-[200px]"
            :disabled="savePending"
          >
            <Save class="mr-2 h-5 w-5" />
            Сохранить настройки
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  transition-property: transform, box-shadow, background-color, border-color;
  transition-duration: 0.3s;
  transition-timing-function: ease-in-out;
}
</style>
