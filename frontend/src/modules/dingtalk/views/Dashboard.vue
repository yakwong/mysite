<template>
  <div v-loading="loading" class="dingtalk-dashboard">
    <section class="card-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>配置选择</span>
            <el-button type="primary" size="small" :loading="saving" @click="handleSave">保存配置</el-button>
          </div>
        </template>
        <el-form ref="formRef" :model="configForm" label-width="140px" class="config-form">
          <el-form-item label="选择配置：">
            <el-select v-model="currentConfigId" placeholder="请选择配置" @change="handleConfigChange">
              <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="配置名称：" prop="name">
            <el-input v-model="configForm.name" placeholder="示例：集团钉钉" />
          </el-form-item>
          <el-form-item label="租户ID：" prop="tenant_id">
            <el-input v-model="configForm.tenant_id" placeholder="选填" />
          </el-form-item>
          <el-form-item label="App Key：" prop="app_key">
            <el-input v-model="configForm.app_key" placeholder="请输入App Key" clearable />
          </el-form-item>
          <el-form-item label="App Secret：" prop="app_secret">
            <el-input v-model="configForm.app_secret" type="password" placeholder="请输入App Secret" clearable show-password />
          </el-form-item>
          <el-form-item label="Agent ID：" prop="agent_id">
            <el-input v-model="configForm.agent_id" placeholder="请输入Agent ID" clearable />
          </el-form-item>
          <el-form-item label="启用状态：" prop="enabled">
            <el-switch v-model="configForm.enabled" active-text="已启用" inactive-text="已禁用" />
          </el-form-item>
          <el-form-item label="同步用户：" prop="sync_users">
            <el-switch v-model="configForm.sync_users" active-text="开启" inactive-text="关闭" />
          </el-form-item>
          <el-form-item label="同步部门：" prop="sync_departments">
            <el-switch v-model="configForm.sync_departments" active-text="开启" inactive-text="关闭" />
          </el-form-item>
          <el-form-item label="同步考勤：" prop="sync_attendance">
            <el-switch v-model="configForm.sync_attendance" active-text="开启" inactive-text="关闭" />
          </el-form-item>
          <el-form-item label="回调URL：" prop="callback_url">
            <el-input v-model="configForm.callback_url" placeholder="钉钉回调地址" clearable />
          </el-form-item>
          <el-form-item label="回调Token：" prop="callback_token">
            <el-input v-model="configForm.callback_token" placeholder="钉钉回调Token" clearable />
          </el-form-item>
          <el-form-item label="回调AES Key：" prop="callback_aes_key">
            <el-input v-model="configForm.callback_aes_key" placeholder="钉钉回调AES Key" clearable />
          </el-form-item>
          <el-form-item label="备注：" prop="remark">
            <el-input v-model="configForm.remark" type="textarea" :rows="3" placeholder="配置备注信息" />
          </el-form-item>
        </el-form>
      </el-card>
    </section>

    <section class="card-section">
      <el-card class="box-card">
        <template #header>
          <span>同步概览</span>
        </template>
        <el-descriptions title="同步信息" :column="2" border>
          <el-descriptions-item label="最后同步时间">{{ formatDate(syncInfo.lastSyncTime) }}</el-descriptions-item>
          <el-descriptions-item label="同步状态">
            <el-tag :type="statusTagType(syncInfo.status)">{{ statusText(syncInfo.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="同步用户数">{{ syncInfo.userCount }}</el-descriptions-item>
          <el-descriptions-item label="同步部门数">{{ syncInfo.deptCount }}</el-descriptions-item>
          <el-descriptions-item label="考勤记录数">{{ syncInfo.attendanceCount }}</el-descriptions-item>
          <el-descriptions-item label="Token过期时间">{{ formatDate(syncInfo.accessTokenExpiresAt) }}</el-descriptions-item>
          <el-descriptions-item label="最近用户同步">{{ formatDate(syncInfo.lastUserSyncTime) }}</el-descriptions-item>
          <el-descriptions-item label="最近部门同步">{{ formatDate(syncInfo.lastDeptSyncTime) }}</el-descriptions-item>
          <el-descriptions-item label="最近考勤同步">{{ formatDate(syncInfo.lastAttendanceSyncTime) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </section>

    <section class="card-section">
      <el-card class="box-card">
        <template #header>
          <span>API连通性测试</span>
        </template>
        <div class="test-actions">
          <el-button type="success" :loading="testing.connection" @click="handleTestConnection">测试连接</el-button>
          <el-button @click="openAttendancePreviewDialog">预览考勤</el-button>
          <el-button @click="handlePreviewDepartments">预览部门</el-button>
          <el-button @click="handlePreviewUsers">预览用户</el-button>
        </div>
        <el-divider />
        <el-input v-model="testResult" type="textarea" :rows="10" placeholder="预览结果将显示在这里..." readonly />
      </el-card>
    </section>

    <el-dialog v-model="previewDialogVisible" :title="previewTitle" width="720px">
      <el-table :data="previewData" border>
        <el-table-column v-if="previewType === 'department'" prop="dept_id" label="ID" width="100" />
        <el-table-column v-if="previewType === 'department'" prop="name" label="名称" />
        <el-table-column v-if="previewType === 'department'" prop="parent_id" label="父级ID" width="120" />
        <el-table-column v-if="previewType === 'user'" prop="userid" label="用户ID" width="160" />
        <el-table-column v-if="previewType === 'user'" prop="name" label="姓名" width="140" />
        <el-table-column v-if="previewType === 'user'" prop="mobile" label="手机号" width="160" />
        <el-table-column v-if="previewType === 'user'" label="所属部门">
          <template #default="{ row }">{{ formatDeptList(row.dept_id_list ?? row.deptIdList ?? row.dept_list) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="testDialogVisible" title="预览考勤" width="720px">
      <div class="test-dialog-toolbar">
        <el-select
          v-model="testSelectedUserIds"
          multiple
          collapse-tags
          filterable
          remote
          clearable
          reserve-keyword
          placeholder="选择考勤用户"
          :remote-method="handleTestUserSearch"
          :loading="testUserOptionsLoading"
          @visible-change="handleTestUserSelectVisible"
        >
          <el-option
            v-for="item in testUserOptions"
            :key="item.userid"
            :label="formatUserOptionLabel(item)"
            :value="item.userid"
          />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="testDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="testing.attendance" @click="submitPreviewAttendance">获取预览</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import type { FormInstance } from "element-plus";
import dayjs from "dayjs";
import { message } from "@/utils/message";
import { createConfig, getSyncInfo, listConfigs, listRemoteDepartments, listRemoteUsers, previewAttendance, runSyncCommand, updateConfig, type DingTalkConfigForm } from "../api";
import { useDingtalkStore } from "../store/useDingtalkStore";

const store = useDingtalkStore();
const { configs, currentConfigId } = storeToRefs(store);

const formRef = ref<FormInstance>();
const configForm = reactive<DingTalkConfigForm>({
  id: "default",
  name: "默认钉钉配置",
  tenant_id: "",
  app_key: "",
  app_secret: "",
  agent_id: "",
  enabled: false,
  sync_users: true,
  sync_departments: true,
  sync_attendance: false,
  callback_url: "",
  callback_token: "",
  callback_aes_key: "",
  schedule: {},
  remark: ""
});

const syncInfo = reactive({
  status: "",
  message: "",
  lastSyncTime: "",
  lastDeptSyncTime: "",
  lastUserSyncTime: "",
  lastAttendanceSyncTime: "",
  deptCount: 0,
  userCount: 0,
  attendanceCount: 0,
  accessTokenExpiresAt: ""
});

const loading = ref(false);
const saving = ref(false);
const testing = reactive({ connection: false, attendance: false });
const testResult = ref("");
const previewDialogVisible = ref(false);
const previewTitle = ref("预览");
const previewType = ref<"department" | "user">("department");
const previewData = ref<any[]>([]);

const testDialogVisible = ref(false);
const testSelectedUserIds = ref<string[]>([]);
const testUserOptions = ref<any[]>([]);
const testUserOptionsLoading = ref(false);

const statusText = (status: string) => {
  if (!status) return "未同步";
  return status === "success" ? "成功" : status === "failed" ? "失败" : status;
};

const statusTagType = (status: string) => {
  if (status === "success") return "success";
  if (status === "failed") return "danger";
  return "info";
};

const formatDeptList = (value: unknown): string => {
  if (!value) return "-";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "string") return value;
  return "-";
};

const formatUserOptionLabel = (user: any): string => {
  if (!user) return "";
  return user.name || user.userid || "";
};

const formatDate = (value?: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : "-");

const handleConfigChange = async (id: string) => {
  store.setCurrentConfig(id);
  const target = configs.value.find(item => item.id === id);
  if (target) {
    mapConfigToForm(target);
    await loadSyncInfo();
    testSelectedUserIds.value = [];
    testUserOptions.value = [];
    if (testDialogVisible.value) {
      await fetchTestUserOptions();
    }
  }
};

const mapConfigToForm = (cfg: DingTalkConfigForm) => {
  Object.assign(configForm, cfg);
};

const loadConfigs = async () => {
  loading.value = true;
  try {
    const { data } = await listConfigs();
    store.setConfigs(data || []);
    const configList = configs.value;
    if (configList.length) {
      const current = configList.find(item => item.id === currentConfigId.value) || configList[0];
      mapConfigToForm(current);
      await loadSyncInfo();
    } else {
      const created = await createDefaultConfig();
      store.setConfigs([created]);
      mapConfigToForm(created);
    }
  } finally {
    loading.value = false;
  }
};

const createDefaultConfig = async (): Promise<DingTalkConfigForm> => {
  const payload: Partial<DingTalkConfigForm> = { id: "default", name: "默认钉钉配置" };
  const { data } = await createConfig(payload);
  return data;
};

const loadSyncInfo = async () => {
  const { data } = await getSyncInfo(currentConfigId.value);
  Object.assign(syncInfo, data);
};

const handleSave = async () => {
  saving.value = true;
  try {
    const { data } = await updateConfig(configForm.id, configForm);
    const updatedConfigs = configs.value.map(item => (item.id === data.id ? data : item));
    store.setConfigs(updatedConfigs);
    message.success("配置已保存");
  } finally {
    saving.value = false;
  }
};

const handleTestConnection = async () => {
  testing.connection = true;
  try {
    const { data } = await runSyncCommand({ operation: "test_connection" }, configForm.id);
    testResult.value = JSON.stringify(data, null, 2);
    message.success("连接正常");
  } catch (error: any) {
    testResult.value = error?.msg || "测试失败";
    message.error(error?.msg || "测试失败");
  } finally {
    testing.connection = false;
  }
};

const fetchTestUserOptions = async (keyword?: string) => {
  const configId = configForm.id || currentConfigId.value;
  if (!configId) {
    message.warning("请先选择配置");
    testUserOptions.value = [];
    return;
  }
  testUserOptionsLoading.value = true;
  try {
    const params: Record<string, any> = { config_id: configId, limit: 200 };
    if (keyword) params.keyword = keyword;
    const { data } = await listRemoteUsers(params);
    testUserOptions.value = data || [];
  } catch (error: any) {
    testUserOptions.value = [];
    message.error(error?.msg || "获取远程用户失败");
  } finally {
    testUserOptionsLoading.value = false;
  }
};

const handleTestUserSearch = async (query: string) => {
  await fetchTestUserOptions(query);
};

const handleTestUserSelectVisible = async (visible: boolean) => {
  if (!visible) return;
  if (testUserOptions.value.length) return;
  await fetchTestUserOptions();
};

const openAttendancePreviewDialog = async () => {
  testResult.value = "";
  testDialogVisible.value = true;
  await fetchTestUserOptions();
};

const submitPreviewAttendance = async () => {
  if (!testSelectedUserIds.value.length) {
    message.warning("请选择至少一位用户");
    return;
  }
  const configId = configForm.id || currentConfigId.value;
  if (!configId) {
    message.warning("请先选择配置");
    return;
  }
  const start = dayjs().subtract(7, "day").startOf("day").format("YYYY-MM-DDTHH:mm:ss");
  const end = dayjs().endOf("day").format("YYYY-MM-DDTHH:mm:ss");
  testing.attendance = true;
  try {
    const { data } = await previewAttendance({
      config_id: configId,
      start,
      end,
      userIds: testSelectedUserIds.value
    });
    const records = data?.records ?? [];
    testResult.value = JSON.stringify(records, null, 2);
    const count = data?.count ?? records.length;
    message.success(count ? `考勤预览成功，共获取 ${count} 条记录` : "考勤预览成功，未返回记录");
    testDialogVisible.value = false;
  } catch (error: any) {
    testResult.value = error?.msg || "考勤预览失败";
    message.error(error?.msg || "考勤预览失败");
  } finally {
    testing.attendance = false;
  }
};

const handlePreviewDepartments = async () => {
  try {
    const { data } = await listRemoteDepartments({ config_id: configForm.id, limit: 50 });
    previewType.value = "department";
    previewData.value = data || [];
    previewTitle.value = "远程部门预览";
    previewDialogVisible.value = true;
  } catch (error: any) {
    message.error(error?.msg || "获取远程部门失败");
  }
};

const handlePreviewUsers = async () => {
  try {
    const { data } = await listRemoteUsers({ config_id: configForm.id, limit: 50 });
    previewType.value = "user";
    previewData.value = data || [];
    previewTitle.value = "远程用户预览";
    previewDialogVisible.value = true;
  } catch (error: any) {
    message.error(error?.msg || "获取远程用户失败");
  }
};

onMounted(async () => {
  await loadConfigs();
});

watch(
  () => currentConfigId.value,
  async id => {
    if (id !== configForm.id) {
      await handleConfigChange(id);
    }
  }
);

watch(
  () => testDialogVisible.value,
  visible => {
    if (!visible) {
      testSelectedUserIds.value = [];
      testUserOptions.value = [];
    }
  }
);
</script>

<style scoped>
.dingtalk-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-section {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.config-form {
  max-width: 720px;
}

.test-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.test-dialog-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.test-dialog-toolbar .el-select {
  flex: 1;
  min-width: 220px;
}
</style>
