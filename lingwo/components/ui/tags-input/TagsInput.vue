<script setup lang="ts">
import type { TagsInputRootEmits, TagsInputRootProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TagsInputRoot, useForwardPropsEmits } from 'reka-ui'
import { cn } from '~/lib/utils'

const MIN_TAG_LENGTH = 3
const MAX_TAG_LENGTH = 50

const props = withDefaults(
  defineProps<TagsInputRootProps & { class?: HTMLAttributes['class'] }>(),
  {
    // Тег добавляется только по Enter или при потере фокуса (клик/тап вне поля).
    delimiter: '\n',
    addOnBlur: true,
    addOnPaste: false,
    addOnTab: false,
    max: 3,
  },
)
const emits = defineEmits<TagsInputRootEmits & { invalid: [message: string] }>()

const delegatedProps = reactiveOmit(props, 'class')
const forwarded = useForwardPropsEmits(delegatedProps, emits)

function onUpdate(newVal: (string | number)[]) {
  const valid: string[] = []
  let invalidMessage = ''
  for (const v of newVal) {
    const s = (typeof v === 'string' ? v : String(v)).trim()
    if (s.length < MIN_TAG_LENGTH) {
      invalidMessage = 'Раздел: минимум 3 символа'
      continue
    }
    if (s.length > MAX_TAG_LENGTH) {
      invalidMessage = 'Раздел: максимум 50 символов'
      continue
    }
    valid.push(s)
  }
  if (invalidMessage) emits('invalid', invalidMessage)
  emits('update:modelValue', valid)
}
</script>

<template>
  <TagsInputRoot
    v-bind="forwarded"
    :model-value="modelValue"
    @update:model-value="onUpdate"
    :class="cn(
      'flex min-h-9 w-full flex-wrap items-center gap-1.5 rounded-md border border-input bg-transparent px-3 py-1.5 text-base shadow-xs transition-[color,box-shadow] outline-none focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm',
      props.class,
    )"
  >
    <slot />
  </TagsInputRoot>
</template>
