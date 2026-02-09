<script setup lang="ts">
import type { TagsInputInputProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TagsInputInput } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = defineProps<TagsInputInputProps & { class?: HTMLAttributes['class'] }>()
const delegatedProps = reactiveOmit(props, 'class')
</script>

<template>
  <TagsInputInput
    v-bind="delegatedProps"
    :class="cn(
      'min-w-[80px] flex-1 bg-transparent py-1 outline-none placeholder:text-muted-foreground',
      props.class,
    )"
  />
</template>
