<template>
  <div class="dingtalk-users">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="在职人员" name="active">
        <div class="toolbar">
          <el-select v-model="filters.config_id" placeholder="选择配置" style="width: 220px" @change="handleConfigChange">
            <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
          </el-select>
          <el-input v-model="filters.keyword" placeholder="姓名/手机号" clearable @clear="handleReload" @keyup.enter="handleReload" />
          <el-button type="primary" :loading="loading" @click="handleReload">查询</el-button>
          <el-button type="success" :loading="syncing" @click="handleSyncActive">同步人员数据</el-button>
          <el-button @click="openLogs">查看同步日志</el-button>
        </div>
        <el-table v-loading="loading" :data="users" border stripe>
          <el-table-column prop="userid" label="用户ID" width="200" />
          <el-table-column prop="name" label="姓名" width="160" />
          <el-table-column prop="mobile" label="手机号" width="160">
            <template #default="{ row }">{{ formatMobile(row.mobile) }}</template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="dept_names" label="部门" width="220">
            <template #default="{ row }">
              {{ (row.dept_names?.length ? row.dept_names : row.dept_ids)?.join(" / ") || "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="active" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.active ? 'success' : 'info'">{{ row.active ? "有效" : "禁用" }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination">
          <el-pagination background layout="prev, pager, next" :page-size="pagination.size" :current-page="pagination.page" :total="pagination.total" @current-change="handlePageChange" />
        </div>
      </el-tab-pane>
      <el-tab-pane label="离职人员" name="dimission">
        <div class="toolbar">
          <el-select v-model="filters.config_id" placeholder="选择配置" style="width: 220px" @change="handleConfigChange">
            <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
          </el-select>
          <el-input v-model="dimissionFilters.keyword" placeholder="姓名/手机号/用户ID" clearable @clear="handleDimissionReload" @keyup.enter="handleDimissionReload" />
          <el-button type="primary" :loading="dimissionLoading" @click="handleDimissionReload">查询</el-button>
          <el-button type="warning" :loading="dimissionSyncing" @click="handleSyncDimission">同步离职人员</el-button>
          <el-button @click="openLogs">查看同步日志</el-button>
        </div>
        <el-table v-loading="dimissionLoading" :data="dimissionUsers" border stripe>
          <el-table-column prop="userid" label="用户ID" width="200" />
          <el-table-column prop="name" label="姓名" width="160" />
          <el-table-column prop="mobile" label="手机号" width="160">
            <template #default="{ row }">{{ formatMobile(row.mobile) }}</template>
          </el-table-column>
          <el-table-column prop="main_dept_name" label="主部门" width="200" />
          <el-table-column prop="last_work_day" label="最后工作日" width="140">
            <template #default="{ row }">{{ formatDateOnly(row.last_work_day) }}</template>
          </el-table-column>
          <el-table-column prop="leave_time" label="离职时间" width="180">
            <template #default="{ row }">{{ formatDate(row.leave_time) }}</template>
          </el-table-column>
          <el-table-column prop="leave_reason" label="离职原因" show-overflow-tooltip>
            <template #default="{ row }">{{ formatDimissionReason(row) }}</template>
          </el-table-column>
          <el-table-column label="离职状态" width="120">
            <template #default="{ row }">
              <el-tag :type="dimissionStatusMeta(row.status).type">{{ dimissionStatusMeta(row.status).label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="handover_userid" label="交接人" width="160" />
        </el-table>
        <div class="pagination">
          <el-pagination background layout="prev, pager, next" :page-size="dimissionPagination.size" :current-page="dimissionPagination.page" :total="dimissionPagination.total" @current-change="handleDimissionPageChange" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="logsVisible" :title="logDrawerTitle" size="60%">
      <el-table v-loading="logsLoading" :data="logs" border stripe>
        <el-table-column prop="create_time" label="时间" width="180">
          <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
        </el-table-column>
        <el-table-column prop="statusLabel" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100" />
        <el-table-column prop="message" label="摘要" show-overflow-tooltip />
      </el-table>
      <div class="logs-pagination">
        <el-pagination background layout="prev, pager, next" :page-size="logsPagination.size" :total="logsPagination.total" :current-page="logsPagination.page" @current-change="handleLogPageChange" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import dayjs from "dayjs";
import { message } from "@/utils/message";
import { listConfigs, listDimissionUsers, listLogs, listUsers, runSyncCommand, type DingTalkDimissionUser, type DingTalkLog, type DingTalkUser } from "../api";
import { useDingtalkStore } from "../store/useDingtalkStore";

const store = useDingtalkStore();
const { configs, currentConfigId } = storeToRefs(store);

const loading = ref(false);
const syncing = ref(false);
const users = ref<DingTalkUser[]>([]);
const logsVisible = ref(false);
const logsLoading = ref(false);
const logs = ref<DingTalkLog[]>([]);
const logsPagination = reactive({ page: 1, size: 10, total: 0 });
const pagination = reactive({ page: 1, size: 10, total: 0 });
const filters = reactive({ config_id: "", keyword: "" });
const activeTab = ref<"active" | "dimission">("active");
const dimissionLoading = ref(false);
const dimissionSyncing = ref(false);
const dimissionUsers = ref<DingTalkDimissionUser[]>([]);
const dimissionPagination = reactive({ page: 1, size: 10, total: 0 });
const dimissionFilters = reactive({ keyword: "" });
const dimissionInitialized = ref(false);
const currentOperation = computed(() => (activeTab.value === "active" ? "sync_users" : "sync_dimission_users"));
const logDrawerTitle = computed(() => (activeTab.value === "active" ? "在职人员同步日志" : "离职人员同步日志"));

const dimissionStatusMeta = (status: number | null | undefined) => {
  const mapping: Record<number, { label: string; type: "success" | "warning" | "info" | "danger" }> = {
    1: { label: "待离职", type: "warning" },
    2: { label: "已离职", type: "info" },
    3: { label: "已交接", type: "success" }
  };
  return mapping[Number(status)] ?? { label: "未知", type: "info" };
};

const formatDimissionReason = (row: DingTalkDimissionUser) => {
  if (row.leave_reason) return row.leave_reason;
  if (row.voluntary_reasons?.length) return row.voluntary_reasons.join("、");
  if (row.passive_reasons?.length) return row.passive_reasons.join("、");
  return "-";
};

const formatMobile = (mobile?: string | null) => {
  if (!mobile) return "-";
  const digits = mobile.replace(/\D/g, "");
  if (!digits) return "-";
  if (digits.length >= 11) {
    return digits.slice(-11);
  }
  return digits;
};

type KeywordField = "name" | "mobile" | "userid";

const detectKeywordField = (keyword: string, fields: KeywordField[]): KeywordField | null => {
  const trimmed = keyword.trim();
  if (!trimmed) return null;
  const compact = trimmed.replace(/\s+/g, "");
  const hasChinese = /[\u4e00-\u9fa5]/.test(compact);
  const hasLetters = /[a-zA-Z]/.test(compact);
  const digitCount = (compact.match(/\d/g) || []).length;

  if (hasChinese && fields.includes("name")) return "name";
  if (!hasLetters && digitCount >= 4 && fields.includes("mobile")) return "mobile";
  if (hasLetters && digitCount > 0 && fields.includes("userid")) return "userid";
  if (hasLetters && fields.includes("name")) return "name";
  if (fields.includes("name")) return "name";
  if (fields.includes("userid")) return "userid";
  if (fields.includes("mobile")) return "mobile";
  return null;
};

const assignKeywordParam = (params: Record<string, any>, keyword: string, fields: KeywordField[]) => {
  const target = detectKeywordField(keyword, fields);
  if (!target) return;
  params[target] = keyword.trim();
};

const loadConfigs = async () => {
  if (!configs.value.length) {
    const { data } = await listConfigs();
    store.setConfigs(data || []);
  }
  filters.config_id = store.ensureCurrentConfigId(filters.config_id);
};

const loadUsers = async () => {
  loading.value = true;
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    if (!configId) {
      users.value = [];
      pagination.total = 0;
      return;
    }
    const params: Record<string, any> = {
      config_id: configId,
      page: pagination.page,
      size: pagination.size
    };
    if (filters.keyword) {
      assignKeywordParam(params, filters.keyword, ["name", "mobile"]);
    }
    const { data, total } = await listUsers(params);
    users.value = data || [];
    pagination.total = total || 0;
  } catch (error: any) {
    message.error(error?.msg || "加载用户失败");
  } finally {
    loading.value = false;
  }
};

const loadLogs = async (page = logsPagination.page, operation = currentOperation.value) => {
  logsLoading.value = true;
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    if (!configId) {
      logs.value = [];
      logsPagination.total = 0;
      return;
    }
    const { data, total } = await listLogs({ config_id: configId, operation, page, size: logsPagination.size });
    logs.value = data || [];
    logsPagination.total = total || 0;
  } finally {
    logsLoading.value = false;
  }
};

const handleReload = async () => {
  pagination.page = 1;
  await loadUsers();
};

const handleConfigChange = async (id: string) => {
  filters.config_id = store.ensureCurrentConfigId(id);
  if (activeTab.value === "dimission") {
    await handleDimissionReload();
  } else {
    await handleReload();
  }
};

const handlePageChange = async (page: number) => {
  pagination.page = page;
  await loadUsers();
};

const handleLogPageChange = async (page: number) => {
  logsPagination.page = page;
  await loadLogs(page, currentOperation.value);
};

const ensureSyncSuccess = (result: { success?: boolean; msg?: string }) => {
  if (!result?.success) {
    const error = new Error(result?.msg || "同步失败");
    throw error;
  }
  return result;
};

const handleSyncActive = async () => {
  const configId = store.ensureCurrentConfigId(filters.config_id);
  filters.config_id = configId;
  if (!configId) {
    message.warning("请先选择配置");
    return;
  }
  syncing.value = true;
  try {
    const res = await runSyncCommand({ operation: "sync_users" }, configId);
    ensureSyncSuccess(res);
    message.success("已触发人员同步任务");
    await loadUsers();
    if (logsVisible.value) {
      await loadLogs();
    }
  } catch (error: any) {
    message.error(error?.message || error?.msg || "同步人员失败");
  } finally {
    syncing.value = false;
  }
};

const handleSyncDimission = async () => {
  const configId = store.ensureCurrentConfigId(filters.config_id);
  filters.config_id = configId;
  if (!configId) {
    message.warning("请先选择配置");
    return;
  }
  dimissionSyncing.value = true;
  try {
    const res = await runSyncCommand({ operation: "sync_dimission_users" }, configId);
    ensureSyncSuccess(res);
    message.success("已触发离职人员同步任务");
    await loadDimissionUsers();
    if (logsVisible.value) {
      await loadLogs(undefined, currentOperation.value);
    }
  } catch (error: any) {
    message.error(error?.message || error?.msg || "同步离职人员失败");
  } finally {
    dimissionSyncing.value = false;
  }
};

const openLogs = async () => {
  logsVisible.value = true;
  logsPagination.page = 1;
  await loadLogs(1, currentOperation.value);
};

const formatDate = (value?: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : "-");
const formatDateOnly = (value?: string | null) => (value ? dayjs(value).format("YYYY-MM-DD") : "-");

const loadDimissionUsers = async () => {
  dimissionLoading.value = true;
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    if (!configId) {
      dimissionUsers.value = [];
      dimissionPagination.total = 0;
      return;
    }
    const params: Record<string, any> = {
      config_id: configId,
      page: dimissionPagination.page,
      size: dimissionPagination.size
    };
    if (dimissionFilters.keyword) {
      assignKeywordParam(params, dimissionFilters.keyword, ["name", "mobile", "userid"]);
    }
    const { data, total } = await listDimissionUsers(params);
    dimissionUsers.value = data || [];
    dimissionPagination.total = total || 0;
  } catch (error: any) {
    message.error(error?.msg || "加载离职人员失败");
  } finally {
    dimissionLoading.value = false;
  }
};

const handleDimissionReload = async () => {
  dimissionPagination.page = 1;
  await loadDimissionUsers();
};

const handleDimissionPageChange = async (page: number) => {
  dimissionPagination.page = page;
  await loadDimissionUsers();
};

watch(activeTab, async tab => {
  if (tab === "dimission") {
    if (!dimissionInitialized.value) {
      dimissionInitialized.value = true;
      await loadDimissionUsers();
    }
  } else {
    await loadUsers();
  }
});

onMounted(async () => {
  await loadConfigs();
  await loadUsers();
});

watch(
  () => currentConfigId.value,
  async id => {
    if (id) {
      filters.config_id = store.ensureCurrentConfigId(id);
      await handleReload();
      if (dimissionInitialized.value) {
        await handleDimissionReload();
      }
    }
  }
);
</script>

<style scoped>
.dingtalk-users {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

.logs-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
