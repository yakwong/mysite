<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-4">
      <el-form :inline="true" :model="form" label-width="90px" @submit.prevent>
        <el-form-item label="薪资规则">
          <el-select v-model="form.ruleId" placeholder="选择规则" clearable style="width: 200px">
            <el-option v-for="rule in ruleList" :key="rule.id" :label="rule.name" :value="rule.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="发薪周期">
          <el-date-picker v-model="form.period" type="monthrange" unlink-panels range-separator="至" start-placeholder="开始月份" end-placeholder="结束月份" format="YYYY-MM" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="员工">
          <el-select v-model="form.employeeIds" multiple filterable collapse-tags placeholder="选择员工" style="width: 260px">
            <el-option v-for="emp in employeeList" :key="emp.id" :label="`${emp.name}(${emp.job_number})`" :value="emp.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleFetch">查询</el-button>
          <el-button type="success" :loading="loading" @click="handleGenerate">计算薪资</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="recordList" border stripe :loading="loading">
        <el-table-column type="expand">
          <template #default="{ row }">
            <el-descriptions title="薪资明细" :column="2" border>
              <el-descriptions-item label="基础工资">{{ row.detail?.base ?? row.gross_salary }}</el-descriptions-item>
              <el-descriptions-item label="固定补贴">{{ row.detail?.allowance ?? 0 }}</el-descriptions-item>
              <el-descriptions-item label="加班工资">{{ row.detail?.overtime ?? 0 }}</el-descriptions-item>
              <el-descriptions-item label="扣减合计">{{ row.deductions }}</el-descriptions-item>
              <el-descriptions-item label="计税工资">{{ row.detail?.taxable ?? row.gross_salary }}</el-descriptions-item>
              <el-descriptions-item label="个税">{{ row.tax }}</el-descriptions-item>
            </el-descriptions>
          </template>
        </el-table-column>
        <el-table-column label="员工" prop="employeeName" min-width="150" />
        <el-table-column label="工号" prop="employeeJobNumber" min-width="120" />
        <el-table-column label="规则" prop="ruleName" min-width="150" />
        <el-table-column label="周期" min-width="220">
          <template #default="{ row }">{{ row.period_start }} ~ {{ row.period_end }}</template>
        </el-table-column>
        <el-table-column label="应发" prop="gross_salary" min-width="120" />
        <el-table-column label="扣减" prop="deductions" min-width="120" />
        <el-table-column label="个税" prop="tax" min-width="120" />
        <el-table-column label="实发" prop="net_salary" min-width="120" />
        <el-table-column label="状态" prop="statusLabel">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import dayjs from "dayjs";
import { computed, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useHrStoreHook } from "@/store/modules/hr";

const hrStore = useHrStoreHook();
const form = reactive({
  ruleId: "",
  period: [] as string[],
  employeeIds: [] as string[]
});

const loading = computed(() => hrStore.loading);
const ruleList = computed(() => hrStore.payrollRules);
const employeeList = computed(() => hrStore.employees);
const recordList = computed(() => hrStore.payrollRecords);

const ensureInitialize = async () => {
  if (!ruleList.value.length) await hrStore.fetchPayrollRules();
  if (!employeeList.value.length) await hrStore.fetchEmployees();
  if (!form.period.length) {
    const start = dayjs().startOf("month").format("YYYY-MM-DD");
    const end = dayjs().endOf("month").format("YYYY-MM-DD");
    form.period = [start, end];
  }
};

const handleFetch = async () => {
  await ensureInitialize();
  const params: Record<string, any> = {};
  if (form.ruleId) params.rule = form.ruleId;
  if (form.period.length === 2) {
    params.start = form.period[0];
    params.end = form.period[1];
  }
  await hrStore.fetchPayrollRecords(params);
};

const handleGenerate = async () => {
  if (!form.ruleId) {
    ElMessage.warning("请选择薪资规则");
    return;
  }
  if (!form.employeeIds.length) {
    ElMessage.warning("请选择员工");
    return;
  }
  if (form.period.length !== 2) {
    ElMessage.warning("请选择发薪周期");
    return;
  }
  await hrStore.calculatePayroll({
    ruleId: form.ruleId,
    employeeIds: form.employeeIds,
    periodStart: form.period[0],
    periodEnd: form.period[1]
  });
};

const statusType = (status: number) => {
  if (status === 3) return "success";
  if (status === 2) return "warning";
  return "info";
};

onMounted(() => {
  void handleFetch();
});
</script>

<style scoped lang="scss">
.page-container {
  padding: 16px;

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
