<template>
  <div v-loading="loading" class="maincontent">
    <!-- 钉钉API配置区域 -->
    <div class="config-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>钉钉API配置</span>
            <el-button type="primary" size="small" :loading="saving" @click="handleSave">保存配置</el-button>
          </div>
        </template>

        <el-form ref="formRef" :model="configForm" label-width="140px" class="config-form">
          <el-form-item label="App Key：" prop="appKey">
            <el-input v-model="configForm.appKey" placeholder="请输入钉钉应用的App Key" clearable />
          </el-form-item>

          <el-form-item label="App Secret：" prop="appSecret">
            <el-input v-model="configForm.appSecret" type="password" placeholder="请输入钉钉应用的App Secret" clearable show-password />
          </el-form-item>

          <el-form-item label="Agent ID：" prop="agentId">
            <el-input v-model="configForm.agentId" placeholder="请输入钉钉应用的Agent ID" clearable />
          </el-form-item>

          <el-form-item label="启用状态：" prop="enabled">
            <el-switch v-model="configForm.enabled" active-text="已启用" inactive-text="已禁用" />
          </el-form-item>

          <el-form-item label="同步用户：" prop="syncUsers">
            <el-switch v-model="configForm.syncUsers" active-text="开启" inactive-text="关闭" />
          </el-form-item>

          <el-form-item label="同步部门：" prop="syncDepartments">
            <el-switch v-model="configForm.syncDepartments" active-text="开启" inactive-text="关闭" />
          </el-form-item>

          <el-form-item label="回调URL：" prop="callbackUrl">
            <el-input v-model="configForm.callbackUrl" placeholder="钉钉回调地址（选填）" clearable />
          </el-form-item>

          <el-form-item label="备注：" prop="remark">
            <el-input v-model="configForm.remark" type="textarea" :rows="3" placeholder="配置备注信息" />
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 同步操作区域 -->
    <div class="sync-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>数据同步</span>
          </div>
        </template>

        <div class="sync-buttons">
          <el-button type="primary" :icon="useRenderIcon('ri:user-line')" :loading="syncing.users" @click="handleSyncUsers">同步用户数据</el-button>
          <el-button type="primary" :icon="useRenderIcon('ri:building-line')" :loading="syncing.departments" @click="handleSyncDepartments">同步部门数据</el-button>
          <el-button type="warning" :icon="useRenderIcon('ri:refresh-line')" :loading="syncing.full" @click="handleFullSync">全量同步</el-button>
          <el-button type="info" :icon="useRenderIcon('ri:history-line')" @click="handleViewLogs">查看同步日志</el-button>
        </div>

        <el-divider />

        <div class="sync-info">
          <el-descriptions title="同步信息" :column="2" border>
            <el-descriptions-item label="最后同步时间">{{ syncInfo.lastSyncTime || "暂无记录" }}</el-descriptions-item>
            <el-descriptions-item label="同步状态">
              <el-tag :type="syncStatusTagType">{{ syncStatusText }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="同步用户数">{{ syncInfo.userCount || 0 }}</el-descriptions-item>
            <el-descriptions-item label="同步部门数">{{ syncInfo.deptCount || 0 }}</el-descriptions-item>
            <el-descriptions-item label="同步消息" :span="2">{{ syncInfo.message || "暂无信息" }}</el-descriptions-item>
            <el-descriptions-item label="最近用户同步">{{ syncInfo.lastUserSyncTime || "暂无记录" }}</el-descriptions-item>
            <el-descriptions-item label="最近部门同步">{{ syncInfo.lastDeptSyncTime || "暂无记录" }}</el-descriptions-item>
            <el-descriptions-item label="Token过期时间" :span="2">{{ syncInfo.accessTokenExpiresAt || "未生成" }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>
    </div>

    <!-- API测试区域 -->
    <div class="test-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>API连接测试</span>
          </div>
        </template>

        <div class="test-buttons">
          <el-button type="success" :icon="useRenderIcon('ri:link')" :loading="testing" @click="handleTestConnection">测试连接</el-button>
          <el-button type="primary" :icon="useRenderIcon('ri:file-list-line')" @click="handleGetDeptList">获取部门列表</el-button>
          <el-button type="primary" :icon="useRenderIcon('ri:user-search-line')" @click="handleGetUserList">获取用户列表</el-button>
        </div>

        <el-divider />

        <div class="test-result">
          <el-input v-model="testResult" type="textarea" :rows="10" placeholder="测试结果将显示在这里..." readonly />
        </div>
      </el-card>
    </div>

    <el-drawer v-model="logsDrawerVisible" title="同步日志" size="50%">
      <el-table v-loading="logsLoading" :data="logs" border stripe>
        <el-table-column prop="create_time" label="时间" width="190">
          <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
        </el-table-column>
        <el-table-column prop="operationLabel" label="操作" width="140" />
        <el-table-column prop="statusLabel" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="摘要" show-overflow-tooltip />
      </el-table>
      <div class="logs-pagination">
        <el-pagination background layout="prev, pager, next" :page-size="logsPagination.size" :total="logsPagination.total" :current-page="logsPagination.page" @current-change="handleLogPageChange" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { ref, reactive, onMounted, watch, computed } from "vue";
import dayjs from "dayjs";
import type { FormInstance } from "element-plus";
import { message } from "@/utils/message";
import { getDingTalkConfig, updateDingTalkConfig, getDingTalkSyncInfo, testDingTalkConnection, syncDingTalkDepartments, syncDingTalkUsers, syncDingTalkFull, getDingTalkLogs, getDingTalkDepartments, getDingTalkUsers, type DingTalkLog, type DingTalkSyncInfo, type DingTalkConfigForm } from "@/api/dingtalk";

defineOptions({
  name: "dingtalk"
});

const formRef = ref<FormInstance | null>(null);

interface ConfigFormState {
  appKey: string;
  appSecret: string;
  agentId: string;
  enabled: boolean;
  syncUsers: boolean;
  syncDepartments: boolean;
  callbackUrl: string;
  remark: string;
}

const configForm = reactive<ConfigFormState>({
  appKey: "",
  appSecret: "",
  agentId: "",
  enabled: false,
  syncUsers: true,
  syncDepartments: true,
  callbackUrl: "",
  remark: ""
});

const syncInfo = ref({
  status: "",
  message: "",
  lastSyncTime: "",
  lastDeptSyncTime: "",
  lastUserSyncTime: "",
  deptCount: 0,
  userCount: 0,
  accessTokenExpiresAt: ""
});

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const syncing = reactive({ users: false, departments: false, full: false });
const testResult = ref("");
const logsDrawerVisible = ref(false);
const logsLoading = ref(false);
const logs = ref<DingTalkLog[]>([]);
const logsPagination = reactive({ page: 1, size: 10, total: 0 });

const syncStatusText = computed(() => {
  if (!syncInfo.value.status) return "未同步";
  return syncInfo.value.status === "success" ? "成功" : "失败";
});

const syncStatusTagType = computed(() => {
  if (syncInfo.value.status === "success") return "success";
  if (syncInfo.value.status === "failed") return "danger";
  return "info";
});

const formatDate = (value?: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : "");

function mapConfigToForm(config: DingTalkConfigForm) {
  configForm.appKey = config.app_key ?? "";
  configForm.appSecret = config.app_secret ?? "";
  configForm.agentId = config.agent_id ?? "";
  configForm.enabled = Boolean(config.enabled);
  configForm.syncUsers = Boolean(config.sync_users);
  configForm.syncDepartments = Boolean(config.sync_departments);
  configForm.callbackUrl = config.callback_url ?? "";
  configForm.remark = config.remark ?? "";
}

function mapSyncInfo(info: DingTalkSyncInfo) {
  syncInfo.value = {
    status: info.status ?? "",
    message: info.message ?? "",
    lastSyncTime: formatDate(info.lastSyncTime),
    lastDeptSyncTime: formatDate(info.lastDeptSyncTime),
    lastUserSyncTime: formatDate(info.lastUserSyncTime),
    deptCount: info.deptCount ?? 0,
    userCount: info.userCount ?? 0,
    accessTokenExpiresAt: formatDate(info.accessTokenExpiresAt)
  };
}

function extractErrorMessage(error: any, fallback: string) {
  if (error?.response?.data?.msg) return error.response.data.msg;
  if (error?.message) return error.message;
  return fallback;
}

async function loadConfig() {
  loading.value = true;
  try {
    const response = await getDingTalkConfig();
    mapConfigToForm(response.data.config);
    mapSyncInfo(response.data.syncInfo);
  } catch (error) {
    message(extractErrorMessage(error, "加载钉钉配置失败"), { type: "error" });
  } finally {
    loading.value = false;
  }
}

async function refreshSyncInfo() {
  try {
    const response = await getDingTalkSyncInfo();
    mapSyncInfo(response.data);
  } catch (error) {
    message(extractErrorMessage(error, "获取同步信息失败"), { type: "error" });
  }
}

async function handleSave() {
  if (saving.value) return;
  saving.value = true;
  try {
    const payload = {
      app_key: configForm.appKey,
      app_secret: configForm.appSecret,
      agent_id: configForm.agentId,
      enabled: configForm.enabled,
      sync_users: configForm.syncUsers,
      sync_departments: configForm.syncDepartments,
      callback_url: configForm.callbackUrl,
      remark: configForm.remark
    };
    await updateDingTalkConfig(payload);
    message("配置已保存", { type: "success" });
    await refreshSyncInfo();
  } catch (error) {
    message(extractErrorMessage(error, "保存配置失败"), { type: "error" });
  } finally {
    saving.value = false;
  }
}

async function handleTestConnection() {
  if (testing.value) return;
  testing.value = true;
  testResult.value = "正在测试连接...";
  try {
    const response = await testDingTalkConnection();
    const { accessToken, expiresAt } = response.data;
    testResult.value = `连接成功\nAccessToken: ${accessToken}\n过期时间: ${formatDate(expiresAt) || "未知"}`;
    message("连接测试成功", { type: "success" });
    await refreshSyncInfo();
    await refreshLogsIfVisible();
  } catch (error) {
    testResult.value = extractErrorMessage(error, "连接测试失败");
    message(testResult.value, { type: "error" });
    await refreshLogsIfVisible();
  } finally {
    testing.value = false;
  }
}

async function handleSyncUsers() {
  if (syncing.users) return;
  syncing.users = true;
  try {
    const response = await syncDingTalkUsers();
    message(response.msg || "用户同步完成", { type: "success" });
    await refreshSyncInfo();
    await refreshLogsIfVisible();
  } catch (error) {
    message(extractErrorMessage(error, "用户同步失败"), { type: "error" });
    await refreshLogsIfVisible();
  } finally {
    syncing.users = false;
  }
}

async function handleSyncDepartments() {
  if (syncing.departments) return;
  syncing.departments = true;
  try {
    const response = await syncDingTalkDepartments();
    message(response.msg || "部门同步完成", { type: "success" });
    await refreshSyncInfo();
    await refreshLogsIfVisible();
  } catch (error) {
    message(extractErrorMessage(error, "部门同步失败"), { type: "error" });
    await refreshLogsIfVisible();
  } finally {
    syncing.departments = false;
  }
}

async function handleFullSync() {
  if (syncing.full) return;
  syncing.full = true;
  try {
    const response = await syncDingTalkFull();
    message(response.msg || "全量同步完成", { type: "success" });
    await refreshSyncInfo();
    await refreshLogsIfVisible();
  } catch (error) {
    message(extractErrorMessage(error, "全量同步失败"), { type: "error" });
    await refreshLogsIfVisible();
  } finally {
    syncing.full = false;
  }
}

async function handleGetDeptList() {
  testResult.value = "正在获取部门列表...";
  try {
    const response = await getDingTalkDepartments({ source: "remote", limit: 20 });
    if (!response.success) {
      throw new Error(response.msg || "获取部门列表失败");
    }
    const list = Array.isArray(response.data) ? response.data : [];
    const preview = list.slice(0, 10);
    testResult.value = `部门总数：${response.total ?? list.length}\n预览：\n${JSON.stringify(preview, null, 2)}`;
  } catch (error) {
    testResult.value = extractErrorMessage(error, "获取部门列表失败");
  }
}

async function handleGetUserList() {
  testResult.value = "正在获取用户列表...";
  try {
    const response = await getDingTalkUsers({ page: 1, size: 20 });
    const preview = response.data.slice(0, 10);
    testResult.value = `用户总数：${response.total}\n预览：\n${JSON.stringify(preview, null, 2)}`;
  } catch (error) {
    testResult.value = extractErrorMessage(error, "获取用户列表失败");
  }
}

async function fetchLogs(page = 1) {
  logsLoading.value = true;
  try {
    const response = await getDingTalkLogs({ page, size: logsPagination.size });
    logs.value = response.data;
    logsPagination.page = response.page;
    logsPagination.total = response.total;
  } catch (error) {
    message(extractErrorMessage(error, "获取同步日志失败"), { type: "error" });
  } finally {
    logsLoading.value = false;
  }
}

async function refreshLogsIfVisible() {
  if (logsDrawerVisible.value) {
    await fetchLogs(logsPagination.page);
  }
}

function handleViewLogs() {
  logsDrawerVisible.value = true;
}

async function handleLogPageChange(page: number) {
  logsPagination.page = page;
  await fetchLogs(page);
}

watch(logsDrawerVisible, visible => {
  if (visible) {
    fetchLogs(1);
  }
});

onMounted(() => {
  loadConfig();
});
</script>

<style lang="scss" scoped>
.maincontent {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 141px);
  padding: 16px;
  overflow-y: auto;
}

.config-section,
.sync-section,
.test-section {
  .box-card {
    width: 100%;
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  span {
    font-size: 16px;
    font-weight: 600;
  }
}

.config-form {
  max-width: 800px;
}

.sync-buttons,
.test-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.sync-info {
  margin-top: 16px;
}

.test-result {
  margin-top: 16px;
}

::v-deep(.el-descriptions__label) {
  font-weight: 500;
}

.logs-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
