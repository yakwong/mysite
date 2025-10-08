import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { DingTalkConfigForm } from "../api";

export const useDingtalkStore = defineStore("dingtalk", () => {
  const configs = ref<DingTalkConfigForm[]>([]);
  const currentConfigId = ref<string>("");

  const getConfigById = (id?: string) => configs.value.find(item => item.id === id);

  const ensureCurrentConfigId = (preferredId?: string) => {
    if (preferredId && getConfigById(preferredId)) {
      currentConfigId.value = preferredId;
      return preferredId;
    }

    if (currentConfigId.value && getConfigById(currentConfigId.value)) {
      return currentConfigId.value;
    }

    if (configs.value.length) {
      currentConfigId.value = configs.value[0].id;
      return currentConfigId.value;
    }

    currentConfigId.value = "";
    return "";
  };

  const setConfigs = (items: DingTalkConfigForm[]) => {
    configs.value = Array.isArray(items) ? [...items] : [];
    ensureCurrentConfigId(currentConfigId.value);
  };

  const upsertConfig = (config: DingTalkConfigForm) => {
    const index = configs.value.findIndex(item => item.id === config.id);
    if (index === -1) {
      configs.value = [...configs.value, config];
    } else {
      const next = [...configs.value];
      next.splice(index, 1, config);
      configs.value = next;
    }
    ensureCurrentConfigId(config.id);
  };

  const setCurrentConfig = (id: string) => {
    ensureCurrentConfigId(id);
  };

  const activeConfig = computed(() => getConfigById(currentConfigId.value));

  return {
    configs,
    currentConfigId,
    activeConfig,
    setConfigs,
    upsertConfig,
    setCurrentConfig,
    ensureCurrentConfigId,
    getConfigById
  };
});

