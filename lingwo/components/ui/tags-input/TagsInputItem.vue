<script setup lang="ts">
import type { TagsInputItemProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TagsInputItem } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = defineProps<TagsInputItemProps & { class?: HTMLAttributes['class'] }>()
const delegatedProps = reactiveOmit(props, 'class')
</script>

<template>
  <TagsInputItem
    v-bind="delegatedProps"
    :class="cn(
      'inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2 py-0.5 text-sm font-medium text-primary data-[state=active]:ring-2 data-[state=active]:ring-ring',
      props.class,
    )"
  >
    <slot />
  </TagsInputItem>
</template>
