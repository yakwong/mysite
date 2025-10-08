<template>
  <div v-loading="loading" class="dingtalk-attendance">
    <div class="toolbar">
      <el-select v-model="filters.config_id" placeholder="选择配置" style="width: 220px" @change="handleConfigChange">
        <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
      </el-select>
      <el-input v-model="filters.userid" placeholder="用户ID" clearable @clear="handleReload" @keyup.enter="handleReload" />
      <el-date-picker v-model="filters.range" type="datetimerange" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" start-placeholder="开始时间" end-placeholder="结束时间" @change="handleReload" />
      <el-button type="primary" :loading="loading" @click="handleReload">查询</el-button>
      <el-button type="success" :loading="syncing" @click="openSyncDialog">同步考勤数据</el-button>
      <el-button @click="openLogs">查看同步日志</el-button>
    </div>
    <el-table :data="records" border stripe>
      <el-table-column prop="record_id" label="记录ID" width="200" />
      <el-table-column prop="user_name" label="姓名" width="140">
        <template #default="{ row }">{{ row.user_name || "-" }}</template>
      </el-table-column>
      <el-table-column prop="userid" label="用户ID" width="160" />
      <el-table-column prop="check_type_label" label="类型" width="120">
        <template #default="{ row }">{{ row.check_type_label || row.check_type || "-" }}</template>
      </el-table-column>
      <el-table-column prop="time_result_label" label="结果" width="120">
        <template #default="{ row }">{{ row.time_result_label || row.time_result || "-" }}</template>
      </el-table-column>
      <el-table-column prop="user_check_time" label="打卡时间" width="200" />
      <el-table-column prop="work_date" label="工作日期" width="160" />
      <el-table-column prop="source_type" label="来源" width="120" />
    </el-table>
    <div class="pagination">
      <el-pagination background layout="prev, pager, next" :page-size="pagination.size" :current-page="pagination.page" :total="pagination.total" @current-change="handlePageChange" />
    </div>

    <el-dialog v-model="syncDialogVisible" title="同步考勤" width="480px">
      <el-form label-width="120px">
        <el-form-item label="时间范围">
          <el-date-picker v-model="syncRange" type="datetimerange" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" start-placeholder="开始时间" end-placeholder="结束时间" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="syncDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="syncing" @click="submitSync">同 步</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="logsVisible" title="考勤同步日志" size="60%">
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
import { listAttendance, listConfigs, listLogs, runSyncCommand, type DingTalkAttendanceRecord, type DingTalkLog } from "../api";
import { useDingtalkStore } from "../store/useDingtalkStore";

const store = useDingtalkStore();
const { configs, currentConfigId } = storeToRefs(store);

const loading = ref(false);
const syncing = ref(false);
const records = ref<DingTalkAttendanceRecord[]>([]);
const logsVisible = ref(false);
const logsLoading = ref(false);
const logs = ref<DingTalkLog[]>([]);
const logsPagination = reactive({ page: 1, size: 10, total: 0 });
const syncDialogVisible = ref(false);
const syncRange = ref<string[]>([]);
const pagination = reactive({ page: 1, size: 10, total: 0 });
const filters = reactive<{ config_id: string; userid: string; range: string[] | [] }>({ config_id: "", userid: "", range: [] });

const loadConfigs = async () => {
  if (!configs.value.length) {
    const { data } = await listConfigs();
    store.setConfigs(data || []);
  }
  filters.config_id = store.ensureCurrentConfigId(filters.config_id);
};

const loadAttendance = async () => {
  loading.value = true;
  try {
    const configId = store.ensureCurrentConfigId(filters.config_id);
    filters.config_id = configId;
    if (!configId) {
      records.value = [];
      pagination.total = 0;
      return;
    }
    const params: Record<string, any> = {
      config_id: configId,
      page: pagination.page,
      size: pagination.size
    };
    if (filters.userid) params.userid = filters.userid;
    if (filters.range && filters.range.length === 2) {
      params.start = filters.range[0];
      params.end = filters.range[1];
    }
    const { data, total } = await listAttendance(params);
    records.value = data || [];
    pagination.total = total || 0;
  } catch (error: any) {
    message.error(error?.msg || "加载考勤记录失败");
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
    const { data, total } = await listLogs({ config_id: configId, operation: "sync_attendance", page, size: logsPagination.size });
    logs.value = data || [];
    logsPagination.total = total || 0;
  } finally {
    logsLoading.value = false;
  }
};

const handleReload = async () => {
  pagination.page = 1;
  await loadAttendance();
};

const handleConfigChange = async (id: string) => {
  filters.config_id = store.ensureCurrentConfigId(id);
  await handleReload();
};

const handlePageChange = async (page: number) => {
  pagination.page = page;
  await loadAttendance();
};

const handleLogPageChange = async (page: number) => {
  logsPagination.page = page;
  await loadLogs(page);
};

const openSyncDialog = () => {
  const start = dayjs().startOf("day").format("YYYY-MM-DDTHH:mm:ss");
  const end = dayjs().endOf("day").format("YYYY-MM-DDTHH:mm:ss");
  syncRange.value = [start, end];
  syncDialogVisible.value = true;
};

const submitSync = async () => {
  const configId = store.ensureCurrentConfigId(filters.config_id);
  filters.config_id = configId;
  if (!configId) {
    message.warning("请先选择配置");
    return;
  }
  const range = syncRange.value && syncRange.value.length === 2 ? syncRange.value : [];
  const [start, end] = range.length === 2 ? range : [dayjs().startOf("day").format("YYYY-MM-DDTHH:mm:ss"), dayjs().endOf("day").format("YYYY-MM-DDTHH:mm:ss")];
  if (!start || !end) {
    message.warning("请选择同步时间范围");
    return;
  }
  syncing.value = true;
  try {
    await runSyncCommand({ operation: "sync_attendance", start, end }, configId);
    message.success("已触发考勤同步任务");
    syncDialogVisible.value = false;
    await loadAttendance();
    if (logsVisible.value) {
      await loadLogs();
    }
  } catch (error: any) {
    message.error(error?.msg || "同步考勤失败");
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
  await loadAttendance();
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
.dingtalk-attendance {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
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
