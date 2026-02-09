# Компоненты UI

## Кнопка (Button)

### Использование

\`\`\`vue
<script setup>
import { Button } from '~/components/ui/button'
</script>

<template>
  <Button variant="default">Нажми меня</Button>
  <Button variant="secondary">Вторичная</Button>
  <Button variant="outline">С обводкой</Button>
  <Button variant="ghost">Призрак</Button>
  <Button variant="destructive">Удалить</Button>
</template>
\`\`\`

### Варианты (Variants)
- `default` - Основная кнопка (зеленый фон)
- `secondary` - Вторичная кнопка
- `outline` - Кнопка с обводкой
- `ghost` - Прозрачная кнопка
- `destructive` - Кнопка для опасных действий
- `link` - Кнопка-ссылка

### Размеры (Sizes)
- `default` - Стандартный размер (h-9)
- `sm` - Маленькая (h-8)
- `lg` - Большая (h-10)
- `icon` - Квадратная для иконки (size-9)

### Пропсы
- `variant?: ButtonVariants['variant']` - Вариант стиля
- `size?: ButtonVariants['size']` - Размер кнопки
- `disabled?: boolean` - Отключить кнопку
- `as?: string` - HTML тег (по умолчанию 'button')
- `asChild?: boolean` - Использовать как wrapper

## Поле ввода (Input)

### Использование

\`\`\`vue
<script setup>
import { Input } from '~/components/ui/input'

const email = ref('')
const password = ref('')
</script>

<template>
  <Input 
    v-model="email" 
    type="email" 
    placeholder="Email" 
  />
  
  <Input 
    v-model="password" 
    type="password" 
    placeholder="Пароль"
    autocomplete="on"
  />
</template>
\`\`\`

### Пропсы
- `modelValue?: string | number` - Значение (v-model)
- `defaultValue?: string | number` - Значение по умолчанию
- `type?: string` - Тип input (text, email, password, etc.)
- `placeholder?: string` - Placeholder текст
- `disabled?: boolean` - Отключить поле
- `class?: string` - Дополнительные CSS классы

### Особенности
- Автоматическая фокусировка с кольцом
- Валидация через aria-invalid
- Поддержка темной темы
- Красивые анимации transitions

## Стили

Все компоненты используют:
- **Tailwind CSS 4** для стилизации
- **class-variance-authority** для вариантов
- **tailwind-merge** для объединения классов
- **reka-ui** для accessibility

## Цвета

Компоненты автоматически используют цвета из `assets/css/main.css`:
- Primary: `#6DCE78` (зеленый)
- Focus ring: `#6DCE78` с прозрачностью
- Border: светло-зеленый
- Background: белый

## Адаптивность

Все компоненты полностью адаптивны:
- Автоматическое изменение размеров на мобильных
- Touch-friendly размеры кнопок
- Правильные отступы на всех экранах
