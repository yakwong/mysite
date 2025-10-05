<template>
  <div v-loading="loading" class="dingtalk-settings">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>计划任务与回调配置</span>
          <el-button type="primary" :loading="saving" @click="handleSave">保存设置</el-button>
        </div>
      </template>
      <el-form :model="form" label-width="160px">
        <el-form-item label="选择配置">
          <el-select v-model="form.id" placeholder="选择配置" @change="handleConfigChange">
            <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="考勤同步频率 (cron)">
          <el-input v-model="form.schedule.cron" placeholder="示例：0 0 * * *" />
        </el-form-item>
        <el-form-item label="考勤时间窗口(天)">
          <el-input-number v-model="form.schedule.attendance_window" :min="1" :max="30" />
        </el-form-item>
        <el-form-item label="回调地址">
          <el-input v-model="form.callback_url" placeholder="https://example.com/dingtalk/callback" />
        </el-form-item>
        <el-form-item label="回调Token">
          <el-input v-model="form.callback_token" />
        </el-form-item>
        <el-form-item label="回调AES Key">
          <el-input v-model="form.callback_aes_key" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { storeToRefs } from "pinia";
import { message } from "@/utils/message";
import { listConfigs, updateConfig, type DingTalkConfigForm } from "../api";
import { useDingtalkStore } from "../store/useDingtalkStore";

const store = useDingtalkStore();
const { configs } = storeToRefs(store);

const loading = ref(false);
const saving = ref(false);
const form = reactive<{ id: string; schedule: { cron: string; attendance_window: number }; callback_url: string; callback_token: string; callback_aes_key: string; remark: string }>({
  id: "default",
  schedule: { cron: "0 0 * * *", attendance_window: 1 },
  callback_url: "",
  callback_token: "",
  callback_aes_key: "",
  remark: ""
});

const loadConfigs = async () => {
  loading.value = true;
  try {
    const { data } = await listConfigs();
    store.setConfigs(data || []);
    const list = configs.value;
    if (list.length) {
      mapConfig(list[0]);
    }
  } finally {
    loading.value = false;
  }
};

const mapConfig = (cfg: DingTalkConfigForm) => {
  form.id = cfg.id;
  const schedule = (cfg.schedule || {}) as { cron?: string; attendance_window?: number | string };
  form.schedule.cron = schedule.cron || "0 0 * * *";
  const windowValue = schedule.attendance_window;
  const parsedWindow = typeof windowValue === "number" ? windowValue : Number(windowValue ?? 1);
  form.schedule.attendance_window = Number.isFinite(parsedWindow) && parsedWindow > 0 ? parsedWindow : 1;
  form.callback_url = cfg.callback_url ?? "";
  form.callback_token = cfg.callback_token ?? "";
  form.callback_aes_key = cfg.callback_aes_key ?? "";
  form.remark = cfg.remark ?? "";
};

const handleConfigChange = (id: string) => {
  const target = configs.value.find(item => item.id === id);
  if (target) {
    mapConfig(target);
  }
};

const handleSave = async () => {
  saving.value = true;
  try {
    const attendanceWindowValue = form.schedule.attendance_window;
    const payload: Partial<DingTalkConfigForm> = {
      schedule: {
        cron: form.schedule.cron,
        attendance_window: Number.isFinite(attendanceWindowValue) && attendanceWindowValue > 0 ? attendanceWindowValue : 1
      },
      callback_url: form.callback_url,
      callback_token: form.callback_token,
      callback_aes_key: form.callback_aes_key,
      remark: form.remark
    };
    const { data } = await updateConfig(form.id, payload);
    const updatedConfigs = configs.value.map(item => (item.id === data.id ? data : item));
    store.setConfigs(updatedConfigs);
    message.success("设置已保存");
  } catch (error: any) {
    message.error(error?.msg || "保存失败");
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  await loadConfigs();
});
</script>

<style scoped>
.dingtalk-settings {
  max-width: 720px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
