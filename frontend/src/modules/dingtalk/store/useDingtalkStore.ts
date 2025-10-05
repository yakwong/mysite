import { defineStore } from "pinia";
import { ref } from "vue";
import type { DingTalkConfigForm } from "../api";

export const useDingtalkStore = defineStore("dingtalk", () => {
  const configs = ref<DingTalkConfigForm[]>([]);
  const currentConfigId = ref<string>("default");

  const setConfigs = (items: DingTalkConfigForm[]) => {
    configs.value = items;
    if (!items.find(item => item.id === currentConfigId.value) && items.length) {
      currentConfigId.value = items[0].id;
    }
  };

  const setCurrentConfig = (id: string) => {
    currentConfigId.value = id;
  };

  return {
    configs,
    currentConfigId,
    setConfigs,
    setCurrentConfig
  };
});
