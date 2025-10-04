<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { message } from "@/utils/message";
import { deviceDetection, storageLocal } from "@pureadmin/utils";
import { getSecurityState, toggleLoginNotifier } from "@/api/user";

defineOptions({
  name: "Preferences"
});

type PreferenceKey = "loginNotifier" | "systemMessage" | "todoTask";
type LocalPreferenceKey = Exclude<PreferenceKey, "loginNotifier">;
type PreferenceItem = {
  key: PreferenceKey;
  title: string;
  illustrate: string;
  checked: boolean;
  type: "remote" | "local";
  loading?: boolean;
};

const STORAGE_KEY = "account-settings-preferences";
const storage = storageLocal();
const defaultLocalState: Record<LocalPreferenceKey, boolean> = {
  systemMessage: true,
  todoTask: true
};
const savedLocal = storage.getItem<Record<LocalPreferenceKey, boolean>>(STORAGE_KEY) ?? {};
const localState = reactive<Record<LocalPreferenceKey, boolean>>({
  systemMessage: savedLocal.systemMessage ?? defaultLocalState.systemMessage,
  todoTask: savedLocal.todoTask ?? defaultLocalState.todoTask
});

const loading = ref(true);
const list = ref<PreferenceItem[]>([
  {
    key: "loginNotifier",
    title: "登录提醒",
    illustrate: "开启后检测到新的登录将推送提醒",
    checked: false,
    type: "remote",
    loading: false
  },
  {
    key: "systemMessage",
    title: "系统消息",
    illustrate: "系统消息将以站内信的形式通知",
    checked: localState.systemMessage,
    type: "local"
  },
  {
    key: "todoTask",
    title: "待办任务",
    illustrate: "待办任务将以站内信的形式通知",
    checked: localState.todoTask,
    type: "local"
  }
]);

function persistLocal() {
  storage.setItem(STORAGE_KEY, { ...localState });
}

async function fetchPreferences() {
  loading.value = true;
  try {
    const { data } = await getSecurityState();
    const loginItem = list.value.find(item => item.key === "loginNotifier");
    if (loginItem) {
      loginItem.checked = data.login_notifier_enabled;
    }
  } catch (error) {
    console.error("获取偏好设置失败", error);
    message("获取偏好设置失败，请稍后重试", { type: "error" });
  } finally {
    loading.value = false;
  }
}

async function onChange(val: boolean, item: PreferenceItem) {
  if (item.type === "remote") {
    item.loading = true;
    try {
      await toggleLoginNotifier({ enabled: val });
      message(val ? "已开启登录提醒" : "已关闭登录提醒", { type: "success" });
    } catch (error) {
      item.checked = !val;
      message("更新登录提醒失败，请稍后重试", { type: "error" });
    } finally {
      item.loading = false;
    }
    return;
  }

  const key = item.key as LocalPreferenceKey;
  localState[key] = val;
  persistLocal();
  message(`${item.title}已${val ? "开启" : "关闭"}`, { type: "success" });
}

onMounted(() => {
  fetchPreferences();
});
</script>

<template>
  <div :class="['min-w-[180px]', deviceDetection() ? 'max-w-[100%]' : 'max-w-[70%]']">
    <h3 class="my-8!">偏好设置</h3>
    <el-skeleton v-if="loading" animated :count="3">
      <template #template>
        <div class="py-4">
          <el-skeleton-item variant="text" style="width: 40%" />
          <el-skeleton-item variant="text" style="width: 70%; margin-top: 12px" />
        </div>
      </template>
    </el-skeleton>
    <template v-else>
      <div v-for="item in list" :key="item.key">
        <div class="flex items-center">
          <div class="flex-1">
            <p>{{ item.title }}</p>
            <p class="wp-4">
              <el-text class="mx-1" type="info">
                {{ item.illustrate }}
              </el-text>
            </p>
          </div>
          <el-switch v-model="item.checked" inline-prompt active-text="是" inactive-text="否" :loading="Boolean(item.loading)" @change="val => onChange(val, item)" />
        </div>
        <el-divider />
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.el-divider--horizontal {
  border-top: 0.1px var(--el-border-color) var(--el-border-style);
}
</style>
