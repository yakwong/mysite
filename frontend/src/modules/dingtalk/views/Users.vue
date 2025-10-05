<template>
  <div v-loading="loading" class="dingtalk-users">
    <div class="toolbar">
      <el-select v-model="filters.config_id" placeholder="选择配置" style="width: 220px" @change="handleConfigChange">
        <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="姓名/手机号" clearable @clear="handleReload" @keyup.enter="handleReload" />
      <el-button type="primary" :loading="loading" @click="handleReload">查询</el-button>
      <el-button type="success" :loading="syncing" @click="handleSync">同步人员数据</el-button>
      <el-button @click="openLogs">查看同步日志</el-button>
    </div>
    <el-table :data="users" border stripe>
      <el-table-column prop="userid" label="用户ID" width="200" />
      <el-table-column prop="name" label="姓名" width="160" />
      <el-table-column prop="mobile" label="手机号" width="160" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="dept_ids" label="部门" width="200">
        <template #default="{ row }">{{ row.dept_ids?.join(", ") }}</template>
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

    <el-drawer v-model="logsVisible" title="人员同步日志" size="60%">
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
import { onMounted, reactive, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import dayjs from "dayjs";
import { message } from "@/utils/message";
import { listConfigs, listLogs, listUsers, runSyncCommand, type DingTalkLog, type DingTalkUser } from "../api";
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

const ensureConfigId = () => {
  if (filters.config_id && configs.value.some(item => item.id === filters.config_id)) {
    return filters.config_id;
  }
  if (currentConfigId.value && configs.value.some(item => item.id === currentConfigId.value)) {
    filters.config_id = currentConfigId.value;
    return filters.config_id;
  }
  if (configs.value.length) {
    filters.config_id = configs.value[0].id;
  }
  return filters.config_id;
};

const loadConfigs = async () => {
  if (configs.value.length) {
    ensureConfigId();
    return;
  }
  const { data } = await listConfigs();
  store.setConfigs(data || []);
  ensureConfigId();
};

const loadUsers = async () => {
  loading.value = true;
  try {
    const configId = ensureConfigId();
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
      params.name = filters.keyword;
      params.mobile = filters.keyword;
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

const loadLogs = async (page = logsPagination.page) => {
  logsLoading.value = true;
  try {
    const configId = ensureConfigId();
    if (!configId) {
      logs.value = [];
      logsPagination.total = 0;
      return;
    }
    const { data, total } = await listLogs({ config_id: configId, operation: "sync_users", page, size: logsPagination.size });
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
  filters.config_id = id;
  store.setCurrentConfig(id);
  await handleReload();
};

const handlePageChange = async (page: number) => {
  pagination.page = page;
  await loadUsers();
};

const handleLogPageChange = async (page: number) => {
  logsPagination.page = page;
  await loadLogs(page);
};

const handleSync = async () => {
  const configId = ensureConfigId();
  if (!configId) {
    message.warning("请先选择配置");
    return;
  }
  syncing.value = true;
  try {
    await runSyncCommand({ operation: "sync_users" }, configId);
    message.success("已触发人员同步任务");
    await loadUsers();
    if (logsVisible.value) {
      await loadLogs();
    }
  } catch (error: any) {
    message.error(error?.msg || "同步人员失败");
  } finally {
    syncing.value = false;
  }
};

const openLogs = async () => {
  logsVisible.value = true;
  logsPagination.page = 1;
  await loadLogs(1);
};

const formatDate = (value?: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : "-");

onMounted(async () => {
  await loadConfigs();
  await loadUsers();
});

watch(
  () => currentConfigId.value,
  async id => {
    if (id) {
      filters.config_id = id;
      await handleReload();
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
