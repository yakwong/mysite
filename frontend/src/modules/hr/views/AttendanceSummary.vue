<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-4">
      <el-form :inline="true" :model="form" label-width="90px" @submit.prevent>
        <el-form-item label="考勤规则">
          <el-select v-model="form.ruleId" placeholder="选择规则" clearable style="width: 200px">
            <el-option v-for="rule in ruleList" :key="rule.id" :label="rule.name" :value="rule.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计周期">
          <el-date-picker v-model="form.dateRange" type="daterange" unlink-panels range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="员工">
          <el-select v-model="form.employeeIds" multiple filterable collapse-tags placeholder="选择员工" style="width: 260px">
            <el-option v-for="emp in employeeList" :key="emp.id" :label="`${emp.name}(${emp.job_number})`" :value="emp.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleFetch">查询</el-button>
          <el-button type="success" :loading="loading" @click="handleGenerate">生成统计</el-button>
          <el-button @click="handleMark(2)" :disabled="!selectedRows.length">标记为已确认</el-button>
          <el-button @click="handleMark(1)" :disabled="!selectedRows.length">标记为待确认</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="summaryList" border stripe @selection-change="handleSelectionChange" :loading="loading">
        <el-table-column type="selection" width="50" />
        <el-table-column type="expand">
          <template #default="{ row }">
            <el-table :data="detailRows(row)" size="small" border class="detail-table">
              <el-table-column label="日期" prop="date" min-width="120" />
              <el-table-column label="状态" prop="status" min-width="100" />
              <el-table-column label="迟到(分)" prop="late" min-width="120" />
              <el-table-column label="早退(分)" prop="early" min-width="120" />
              <el-table-column label="加班(小时)" prop="overtime" min-width="140" />
              <el-table-column label="打卡记录" prop="records" min-width="280">
                <template #default="{ row: detail }">
                  <div class="flex flex-col gap-1">
                    <span v-for="record in detail.records" :key="record.id">
                      {{ record.checkedAt }} · {{ record.type }} · {{ record.result }}
                    </span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-table-column>
        <el-table-column label="员工" prop="employeeName" min-width="150" />
        <el-table-column label="工号" prop="employeeJobNumber" min-width="120" />
        <el-table-column label="规则" prop="ruleName" min-width="150" />
        <el-table-column label="周期" min-width="220">
          <template #default="{ row }">{{ row.period_start }} ~ {{ row.period_end }}</template>
        </el-table-column>
        <el-table-column label="应出勤" prop="work_days" />
        <el-table-column label="实出勤" prop="present_days" />
        <el-table-column label="迟到(分)" prop="late_minutes" />
        <el-table-column label="早退(分)" prop="early_leave_minutes" />
        <el-table-column label="缺勤(天)" prop="absence_days" />
        <el-table-column label="加班(小时)" prop="overtime_hours" />
        <el-table-column label="状态" prop="statusLabel">
          <template #default="{ row }">
            <el-tag :type="row.status === 2 ? 'success' : 'warning'">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import dayjs from "dayjs";
import { computed, reactive, ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useHrStoreHook } from "@/store/modules/hr";
import type { AttendanceSummaryItem } from "@/api/hr";

const hrStore = useHrStoreHook();
const form = reactive({
  ruleId: "",
  dateRange: [] as string[],
  employeeIds: [] as string[]
});
const selectedRows = ref<AttendanceSummaryItem[]>([]);

const loading = computed(() => hrStore.loading);
const employeeList = computed(() => hrStore.employees);
const ruleList = computed(() => hrStore.attendanceRules);
const summaryList = computed(() => hrStore.attendanceSummary);

const ensureInitialize = async () => {
  if (!ruleList.value.length) await hrStore.fetchAttendanceRules();
  if (!employeeList.value.length) await hrStore.fetchEmployees();
  if (!form.dateRange.length) {
    const end = dayjs().format("YYYY-MM-DD");
    const start = dayjs().subtract(6, "day").format("YYYY-MM-DD");
    form.dateRange = [start, end];
  }
};

const handleFetch = async () => {
  await ensureInitialize();
  const params: Record<string, any> = {};
  if (form.ruleId) params.rule = form.ruleId;
  if (form.dateRange.length === 2) {
    params.start = form.dateRange[0];
    params.end = form.dateRange[1];
  }
  if (form.employeeIds.length) params.employee = form.employeeIds[0];
  await hrStore.fetchAttendanceSummary(params);
};

const handleGenerate = async () => {
  if (!form.ruleId) {
    ElMessage.warning("请选择考勤规则");
    return;
  }
  if (!form.employeeIds.length) {
    ElMessage.warning("请选择需要统计的员工");
    return;
  }
  if (form.dateRange.length !== 2) {
    ElMessage.warning("请选择统计周期");
    return;
  }
  await hrStore.calculateAttendance({
    ruleId: form.ruleId,
    employeeIds: form.employeeIds,
    start: form.dateRange[0],
    end: form.dateRange[1]
  });
};

const handleSelectionChange = (rows: AttendanceSummaryItem[]) => {
  selectedRows.value = rows;
};

const handleMark = async (status: number) => {
  if (!selectedRows.value.length) return;
  await hrStore.updateAttendanceStatus({
    ids: selectedRows.value.map(item => item.id),
    status
  });
};

const detailRows = (row: AttendanceSummaryItem) => {
  const detail = row.detail || {};
  return Object.keys(detail)
    .sort()
    .map(key => ({
      date: key,
      status: detail[key].status,
      late: detail[key].lateMinutes ?? 0,
      early: detail[key].earlyLeaveMinutes ?? 0,
      overtime: detail[key].overtimeHours ?? 0,
      records: detail[key].records ?? []
    }));
};

onMounted(() => {
  handleFetch();
});
</script>

<style scoped lang="scss">
.page-container {
  padding: 16px;

  .mb-4 {
    margin-bottom: 16px;
  }

  .detail-table {
    margin: 8px 0;
  }
}
</style>
