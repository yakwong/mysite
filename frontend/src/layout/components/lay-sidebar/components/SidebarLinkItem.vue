<script setup lang="ts">
import { computed } from "vue";
import { isUrl } from "@pureadmin/utils";
import { menuType } from "@/layout/types";

const props = defineProps<{
  to: menuType;
}>();

const isExternalLink = computed(() => isUrl(props.to.path) || isUrl(props.to.name));
const getLinkProps = (item: menuType) => {
  if (isExternalLink.value) {
    const href = isUrl(item.path) ? item.path : item.name;
    return {
      href,
      target: "_blank",
      rel: "noopener"
    };
  }
  return {
    to: item.path || "/"
  };
};
</script>

<template>
  <component :is="isExternalLink ? 'a' : 'router-link'" v-bind="getLinkProps(to)">
    <slot />
  </component>
</template>
