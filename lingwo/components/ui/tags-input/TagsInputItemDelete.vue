<script setup lang="ts">
import type { TagsInputItemDeleteProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { X } from 'lucide-vue-next'
import { TagsInputItemDelete } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = defineProps<TagsInputItemDeleteProps & { class?: HTMLAttributes['class'] }>()
const delegatedProps = reactiveOmit(props, 'class')
</script>

<template>
  <TagsInputItemDelete
    v-bind="delegatedProps"
    :class="cn(
      'inline-flex size-4 shrink-0 items-center justify-center rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-1 focus:ring-ring disabled:pointer-events-none disabled:opacity-50',
      props.class,
    )"
  >
    <slot>
      <X class="size-3" />
    </slot>
  </TagsInputItemDelete>
</template>
