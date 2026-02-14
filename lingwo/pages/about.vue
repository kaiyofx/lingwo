<script setup lang="ts">
import { Info, Mail, MessageCircle, Code, Scale, AlertTriangle } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'

useHead({
  title: 'О проекте - Лингво',
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-green-50/30 to-emerald-50/40">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
      <div class="space-y-6">
        <!-- О проекте -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Info class="h-4 w-4 text-primary" />
              </div>
              О проекте
            </CardTitle>
            <CardDescription class="text-gray-600 text-base">
              Лингво — сервис для подготовки школьников к сочинению по русскому языку.
            </CardDescription>
          </CardHeader>
        </Card>

        <!-- Контакты -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Mail class="h-4 w-4 text-primary" />
              </div>
              Контакты
            </CardTitle>
          </CardHeader>
          <CardContent >
            <a
              href="mailto:contact@lingwo.ru"
              class="flex items-center gap-2 text-primary hover:text-primary/80 font-medium transition-colors"
            >
              <Mail class="h-4 w-4 shrink-0" />
              contact@lingwo.ru
            </a>
            <a
              href="https://t.me/kaiyofx"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-2 text-primary hover:text-primary/80 font-medium transition-colors"
            >
              <MessageCircle class="h-4 w-4 shrink-0" />
              https://t.me/kaiyofx
            </a>
          </CardContent>
        </Card>

        <!-- Открытый код -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Code class="h-4 w-4 text-primary" />
              </div>
              Открытый код
            </CardTitle>
          </CardHeader>
          <CardContent>
            <a
              href="https://github.com/kaiyofx/lingwo"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 text-primary hover:text-primary/80 font-medium transition-colors"
            >
              <Code class="h-4 w-4 shrink-0" />
              https://github.com/kaiyofx/lingwo
            </a>
          </CardContent>
        </Card>

        <!-- Юридическая информация -->
        <Card class="border-green-100/50 bg-white shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-gray-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Scale class="h-4 w-4 text-primary" />
              </div>
              Юридическая информация
            </CardTitle>
            <CardDescription class="text-gray-600">
              © {{ new Date().getFullYear() }} Лингво. Все права защищены.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul class="space-y-2 text-sm text-gray-700 list-disc list-inside">
              <li>Проект создан в образовательных целях</li>
              <li>Использует открытые данные ФИПИ</li>
              <li>Не хранит персональные данные без согласия</li>
              <li>Распространяется бесплатно</li>
            </ul>
          </CardContent>
        </Card>

        <!-- Важно -->
        <Card class="border-amber-200 bg-amber-50/50 shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2 text-amber-800">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-200/80">
                <AlertTriangle class="h-4 w-4 text-amber-700" />
              </div>
              Важно
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-amber-900/90 font-medium leading-relaxed">
              Сервис не заменяет школьного учителя, а является вспомогательным инструментом для самостоятельной подготовки.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
