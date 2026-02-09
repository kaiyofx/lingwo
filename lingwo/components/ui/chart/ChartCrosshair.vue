<script setup lang="ts">
import type { BulletLegendItemInterface } from "@unovis/ts"
import { VisCrosshair, VisTooltip } from "@unovis/vue"

const props = withDefaults(defineProps<{
  template?: ((d: any, x: number | Date) => string | undefined) | string
  color?: string | ((d: unknown, i: number) => string)
  colors?: string[]
  index?: string
  items?: BulletLegendItemInterface[]
  customTooltip?: any
}>(), {
  colors: () => [],
  items: () => [],
})

function getColor(d: unknown, i: number) {
  if (typeof props.color === 'function') {
    return props.color(d, i)
  }
  if (typeof props.color === 'string') {
    return props.color
  }
  return props.colors?.[i] ?? "transparent"
}
</script>

<template>
  <VisTooltip :horizontal-shift="20" :vertical-shift="20" />
  <VisCrosshair :template="template" :color="getColor" />
</template>
