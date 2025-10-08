<template>
  <div v-loading="loading" class="dingtalk-departments">
    <div class="toolbar">
      <el-select v-model="filters.config_id" placeholder="选择配置" style="width: 220px" @change="handleConfigChange">
        <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="部门名称" clearable @clear="handleReload" @keyup.enter="handleReload" />
      <el-button type="primary" :loading="loading" @click="handleReload">查询</el-button>
      <el-button type="success" :loading="syncing" @click="handleSync">同步部门数据</el-button>
      <el-button @click="openLogs">查看同步日志</el-button>
      <el-button @click="previewRemote">远程预览</el-button>
    </div>
    <el-table :data="departments" border stripe>
      <el-table-column prop="dept_id" label="ID" width="120" />
      <el-table-column prop="name" label="部门名称" />
      <el-table-column prop="parent_id" label="父级ID" width="120" />
      <el-table-column prop="leader_userid" label="负责人" width="160" />
      <el-table-column prop="dept_type" label="类型" width="120" />
    </el-table>
    <div class="pagination">
      <el-pagination background layout="prev, pager, next" :page-size="pagination.size" :current-page="pagination.page" :total="pagination.total" @current-change="handlePageChange" />
    </div>

    <el-dialog v-model="remoteVisible" title="远程部门预览" width="680px">
      <el-table :data="remoteDepartments" border>
        <el-table-column prop="dept_id" label="ID" width="120" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="parent_id" label="父级ID" width="120" />
      </el-table>
    </el-dialog>

    <el-drawer v-model="logsVisible" title="部门同步日志" size="60%">
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
import { listConfigs, listDepartments, listLogs, listRemoteDepartments, runSyncCommand, type DingTalkDepartment, type DingTalkLog } from "../api";
import { useDingtalkStore } from "../store/useDingtalkStore";

const store = useDingtalkStore();
const { configs, currentConfigId } = storeToRefs(store);

const loading = ref(false);
const syncing = ref(false);
const departments = ref<DingTalkDepartment[]>([]);
const remoteDepartments = ref<Record<string, any>[]>([]);
const remoteVisible = ref(false);
const logsVisible = ref(false);
const logsLoading = ref(false);
const logs = ref<DingTalkLog[]>([]);
const logsPagination = reactive({ page: 1, size: 10, total: 0 });
const pagination = reactive({ page: 1, size: 10, total: 0 });
const filters = reactive({ config_id: "", keyword: "" });

const loadConfigs = async () => {
  if (!configs.value.length) {
    const { data } = await listConfigs();
    store.setConfigs(data || []);
  }
  filters.config_id = store.ensureCurrentConfigId(filters.config_id);
};

const loadDepartments = async () => {
  loading.value = true;
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    if (!configId) {
      departments.value = [];
      pagination.total = 0;
      return;
    }
    const params: Record<string, any> = {
      config_id: configId,
      page: pagination.page,
      size: pagination.size
    };
    if (filters.keyword) params.name = filters.keyword;
    const { data, total } = await listDepartments(params);
    departments.value = data || [];
    pagination.total = total || 0;
  } catch (error: any) {
    message.error(error?.msg || "加载部门列表失败");
  } finally {
    loading.value = false;
  }
};

const loadLogs = async (page = logsPagination.page) => {
  logsLoading.value = true;
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    if (!configId) {
      logs.value = [];
      logsPagination.total = 0;
      return;
    }
    const { data, total } = await listLogs({ config_id: configId, operation: "sync_departments", page, size: logsPagination.size });
    logs.value = data || [];
    logsPagination.total = total || 0;
  } finally {
    logsLoading.value = false;
  }
};

const handleReload = async () => {
  pagination.page = 1;
  await loadDepartments();
};

const handleConfigChange = async (id: string) => {
  filters.config_id = store.ensureCurrentConfigId(id);
  await handleReload();
};

const handlePageChange = async (page: number) => {
  pagination.page = page;
  await loadDepartments();
};

const handleLogPageChange = async (page: number) => {
  logsPagination.page = page;
  await loadLogs(page);
};

const handleSync = async () => {
  const configId = store.ensureCurrentConfigId(filters.config_id);
  filters.config_id = configId;
  if (!configId) {
    message.warning("请先选择配置");
    return;
  }
  syncing.value = true;
  try {
    await runSyncCommand({ operation: "sync_departments" }, configId);
    message.success("已触发部门同步任务");
    await loadDepartments();
    if (logsVisible.value) {
      await loadLogs();
    }
  } catch (error: any) {
    message.error(error?.msg || "同步部门失败");
  } finally {
    syncing.value = false;
  }
};

const previewRemote = async () => {
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    const { data } = await listRemoteDepartments({ config_id: configId, limit: 50 });
    remoteDepartments.value = data || [];
    remoteVisible.value = true;
  } catch (error: any) {
    message.error(error?.msg || "获取远程部门失败");
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
  await loadDepartments();
});

watch(
  () => currentConfigId.value,
  async id => {
    if (id) {
      filters.config_id = store.ensureCurrentConfigId(id);
      await handleReload();
    }
  }
);
</script>

<style scoped>
.dingtalk-departments {
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
