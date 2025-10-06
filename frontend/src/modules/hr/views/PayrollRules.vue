<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-4">
      <el-button type="primary" @click="openDialog()">新增薪资规则</el-button>
    </el-card>

    <el-card shadow="never">
      <el-table :data="ruleList" border stripe>
        <el-table-column label="名称" prop="name" min-width="160" />
        <el-table-column label="加班倍数" prop="overtime_rate" min-width="120" />
        <el-table-column label="迟到扣款/分" prop="late_penalty_per_minute" min-width="150" />
        <el-table-column label="缺勤扣款/天" prop="absence_penalty_per_day" min-width="150" />
        <el-table-column label="个税比例" prop="tax_rate" min-width="120">
          <template #default="{ row }">{{ (Number(row.tax_rate) * 100).toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column label="固定补贴" prop="other_allowance" min-width="120" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-space>
              <el-button type="primary" text size="small" @click="openDialog(row)">编辑</el-button>
              <el-popconfirm title="确认删除该规则？" @confirm="handleDelete(row)">
                <template #reference>
                  <el-button type="danger" text size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="130px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="加班倍数" prop="overtime_rate">
          <el-input-number v-model="form.overtime_rate" :min="1" :step="0.1" :precision="2" />
        </el-form-item>
        <el-form-item label="迟到扣款/分钟" prop="late_penalty_per_minute">
          <el-input-number v-model="form.late_penalty_per_minute" :min="0" :step="1" :precision="2" />
        </el-form-item>
        <el-form-item label="缺勤扣款/天" prop="absence_penalty_per_day">
          <el-input-number v-model="form.absence_penalty_per_day" :min="0" :step="10" :precision="2" />
        </el-form-item>
        <el-form-item label="个税比例(0-1)" prop="tax_rate">
          <el-input-number v-model="form.tax_rate" :min="0" :max="1" :step="0.01" :precision="4" />
        </el-form-item>
        <el-form-item label="额外补贴" prop="other_allowance">
          <el-input-number v-model="form.other_allowance" :min="0" :step="50" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElMessageBox, ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useHrStoreHook } from "@/store/modules/hr";
import type { PayrollRuleItem } from "@/api/hr";

const hrStore = useHrStoreHook();
const formRef = ref<FormInstance>();
const dialogVisible = ref(false);
const submitLoading = ref(false);

const form = reactive({
  id: "",
  name: "",
  description: "",
  overtime_rate: 1.5,
  late_penalty_per_minute: 0,
  absence_penalty_per_day: 0,
  tax_rate: 0.1,
  other_allowance: 0
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入规则名称", trigger: "blur" }],
  overtime_rate: [{ required: true, message: "请输入加班倍数", trigger: "change" }],
  tax_rate: [{ required: true, message: "请输入个税比例", trigger: "change" }]
};

const ruleList = computed(() => hrStore.payrollRules);
const dialogTitle = computed(() => (form.id ? "编辑薪资规则" : "新增薪资规则"));

const fetchRules = () => hrStore.fetchPayrollRules();

const openDialog = (row?: PayrollRuleItem) => {
  if (row) {
    form.id = row.id;
    form.name = row.name;
    form.description = row.description ?? "";
    form.overtime_rate = Number(row.overtime_rate ?? 1);
    form.late_penalty_per_minute = Number(row.late_penalty_per_minute ?? 0);
    form.absence_penalty_per_day = Number(row.absence_penalty_per_day ?? 0);
    form.tax_rate = Number(row.tax_rate ?? 0.1);
    form.other_allowance = Number(row.other_allowance ?? 0);
  } else {
    form.id = "";
    form.name = "";
    form.description = "";
    form.overtime_rate = 1.5;
    form.late_penalty_per_minute = 0;
    form.absence_penalty_per_day = 0;
    form.tax_rate = 0.1;
    form.other_allowance = 0;
  }
  dialogVisible.value = true;
};

const handleSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async valid => {
    if (!valid) return;
    submitLoading.value = true;
    try {
      await hrStore.savePayrollRule({
        id: form.id || undefined,
        name: form.name,
        description: form.description,
        overtime_rate: form.overtime_rate,
        late_penalty_per_minute: form.late_penalty_per_minute,
        absence_penalty_per_day: form.absence_penalty_per_day,
        tax_rate: form.tax_rate,
        other_allowance: form.other_allowance
      });
      dialogVisible.value = false;
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = (row: PayrollRuleItem) => {
  ElMessageBox.confirm(`确认删除规则【${row.name}】？`, "提示", { type: "warning" })
    .then(async () => {
      const res = await hrStore.removePayrollRule(row.id);
      if (!res.success) {
        ElMessage.error(res.msg);
      }
    })
    .catch(() => {
      /* ignore */
    });
};

fetchRules();
</script>

<style scoped lang="scss">
.page-container {
  padding: 16px;

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
