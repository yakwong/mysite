<template>
  <div v-loading="loading" class="dingtalk-logs">
    <div class="toolbar">
      <el-select v-model="filters.config_id" placeholder="选择配置" clearable @change="handleFilterChange">
        <el-option v-for="item in configs" :key="item.id" :label="`${item.name}(${item.id})`" :value="item.id" />
      </el-select>
      <el-select v-model="filters.operation" placeholder="操作类型" clearable @change="handleFilterChange">
        <el-option label="测试连接" value="test_connection" />
        <el-option label="同步部门" value="sync_departments" />
        <el-option label="同步用户" value="sync_users" />
        <el-option label="同步考勤" value="sync_attendance" />
        <el-option label="全量同步" value="full_sync" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable @change="handleFilterChange">
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-select v-model="filters.level" placeholder="级别" clearable @change="handleFilterChange">
        <el-option label="信息" value="info" />
        <el-option label="警告" value="warning" />
        <el-option label="错误" value="error" />
      </el-select>
      <el-button @click="refresh">刷新</el-button>
    </div>
    <el-table :data="logs" border stripe>
      <el-table-column prop="create_time" label="时间" width="180">
        <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
      </el-table-column>
      <el-table-column prop="operationLabel" label="操作" width="140" />
      <el-table-column prop="statusLabel" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.status === 'success' ? 'success' : 'danger'">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="level" label="级别" width="100" />
      <el-table-column prop="message" label="摘要" />
      <el-table-column label="详情" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="showDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination">
      <el-pagination background layout="prev, pager, next" :page-size="pagination.size" :current-page="pagination.page" :total="pagination.total" @current-change="handlePageChange" />
    </div>

    <el-dialog v-model="detailVisible" title="日志详情" width="600px">
      <pre class="log-detail">{{ detailContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import dayjs from "dayjs";
import { message } from "@/utils/message";
import { listConfigs, listLogs, type DingTalkLog } from "../api";
import { useDingtalkStore } from "../store/useDingtalkStore";

const store = useDingtalkStore();
const { configs } = store;

const loading = ref(false);
const logs = ref<DingTalkLog[]>([]);
const pagination = reactive({ page: 1, size: 10, total: 0 });
const filters = reactive({ config_id: "", operation: "", status: "", level: "" });
const detailVisible = ref(false);
const detailContent = ref("{}");

const formatDate = (value?: string | null) => (value ? dayjs(value).format("YYYY-MM-DD HH:mm:ss") : "-");

const loadConfigs = async () => {
  if (configs.length) return;
  const { data } = await listConfigs();
  store.setConfigs(data || []);
};

const loadLogs = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value))
    };
    const { data, total } = await listLogs(params);
    logs.value = data || [];
    pagination.total = total || 0;
  } catch (error: any) {
    message.error(error?.msg || "加载日志失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = async (page: number) => {
  pagination.page = page;
  await loadLogs();
};

const handleFilterChange = async () => {
  pagination.page = 1;
  await loadLogs();
};

const showDetail = (row: DingTalkLog) => {
  detailVisible.value = true;
  detailContent.value = JSON.stringify(row, null, 2);
};

const refresh = async () => {
  await loadLogs();
};

onMounted(async () => {
  await loadConfigs();
  await loadLogs();
});
</script>

<style scoped>
.dingtalk-logs {
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

.log-detail {
  max-height: 320px;
  padding: 16px;
  overflow: auto;
  background: var(--el-color-info-light-9);
}
</style>
