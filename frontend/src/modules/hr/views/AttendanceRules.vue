<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-4">
      <el-space>
        <el-button type="primary" @click="openDialog()">新增考勤规则</el-button>
      </el-space>
    </el-card>

    <el-card shadow="never">
      <el-table :data="ruleList" border stripe>
        <el-table-column label="名称" prop="name" min-width="150" />
        <el-table-column label="上班时间" prop="workday_start" />
        <el-table-column label="下班时间" prop="workday_end" />
        <el-table-column label="允许迟到(分)" prop="allow_late_minutes" />
        <el-table-column label="允许早退(分)" prop="allow_early_minutes" />
        <el-table-column label="缺勤阈值(分)" prop="absence_minutes" />
        <el-table-column label="加班阈值(分)" prop="overtime_start_minutes" />
        <el-table-column label="周末算工作日" prop="weekend_as_workday">
          <template #default="{ row }">
            <el-tag :type="row.weekend_as_workday ? 'success' : 'info'">{{ row.weekend_as_workday ? "是" : "否" }}</el-tag>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="工作时间" required>
          <el-time-picker v-model="form.workday_start" placeholder="上班" format="HH:mm" value-format="HH:mm" />
          <span class="mx-2">-</span>
          <el-time-picker v-model="form.workday_end" placeholder="下班" format="HH:mm" value-format="HH:mm" />
        </el-form-item>
        <el-form-item label="迟到容忍(分)" prop="allow_late_minutes">
          <el-input-number v-model="form.allow_late_minutes" :min="0" />
        </el-form-item>
        <el-form-item label="早退容忍(分)" prop="allow_early_minutes">
          <el-input-number v-model="form.allow_early_minutes" :min="0" />
        </el-form-item>
        <el-form-item label="缺勤阈值(分)" prop="absence_minutes">
          <el-input-number v-model="form.absence_minutes" :min="0" :step="10" />
        </el-form-item>
        <el-form-item label="加班阈值(分)" prop="overtime_start_minutes">
          <el-input-number v-model="form.overtime_start_minutes" :min="0" :step="10" />
        </el-form-item>
        <el-form-item label="工作日设置">
          <el-checkbox v-model="form.weekend_as_workday">周末视为工作日</el-checkbox>
          <div class="mt-2">
            <el-select v-model="form.custom_workdays" multiple placeholder="自定义工作日 (1-7)" style="width: 100%">
              <el-option v-for="day in weekOptions" :key="day.value" :label="day.label" :value="day.value" />
            </el-select>
          </div>
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
import type { AttendanceRuleItem } from "@/api/hr";

const hrStore = useHrStoreHook();
const formRef = ref<FormInstance>();
const dialogVisible = ref(false);
const submitLoading = ref(false);

const form = reactive({
  id: "",
  name: "",
  description: "",
  workday_start: "09:00",
  workday_end: "18:00",
  allow_late_minutes: 5,
  allow_early_minutes: 5,
  absence_minutes: 120,
  overtime_start_minutes: 30,
  weekend_as_workday: false,
  custom_workdays: [] as number[]
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入规则名称", trigger: "blur" }],
  workday_start: [{ required: true, message: "请选择上班时间", trigger: "change" }],
  workday_end: [{ required: true, message: "请选择下班时间", trigger: "change" }]
};

const weekOptions = [
  { value: 1, label: "周一" },
  { value: 2, label: "周二" },
  { value: 3, label: "周三" },
  { value: 4, label: "周四" },
  { value: 5, label: "周五" },
  { value: 6, label: "周六" },
  { value: 7, label: "周日" }
];

const ruleList = computed(() => hrStore.attendanceRules);
const dialogTitle = computed(() => (form.id ? "编辑考勤规则" : "新增考勤规则"));

const fetchRules = () => hrStore.fetchAttendanceRules();

const openDialog = (row?: AttendanceRuleItem) => {
  if (row) {
    form.id = row.id;
    form.name = row.name;
    form.description = row.description ?? "";
    form.workday_start = row.workday_start;
    form.workday_end = row.workday_end;
    form.allow_late_minutes = row.allow_late_minutes;
    form.allow_early_minutes = row.allow_early_minutes;
    form.absence_minutes = row.absence_minutes;
    form.overtime_start_minutes = row.overtime_start_minutes;
    form.weekend_as_workday = row.weekend_as_workday;
    form.custom_workdays = [...(row.custom_workdays || [])];
  } else {
    form.id = "";
    form.name = "";
    form.description = "";
    form.workday_start = "09:00";
    form.workday_end = "18:00";
    form.allow_late_minutes = 5;
    form.allow_early_minutes = 5;
    form.absence_minutes = 120;
    form.overtime_start_minutes = 30;
    form.weekend_as_workday = false;
    form.custom_workdays = [1, 2, 3, 4, 5];
  }
  dialogVisible.value = true;
};

const handleSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async valid => {
    if (!valid) return;
    submitLoading.value = true;
    try {
      await hrStore.saveAttendanceRule({
        id: form.id || undefined,
        name: form.name,
        description: form.description,
        workday_start: form.workday_start,
        workday_end: form.workday_end,
        allow_late_minutes: form.allow_late_minutes,
        allow_early_minutes: form.allow_early_minutes,
        absence_minutes: form.absence_minutes,
        overtime_start_minutes: form.overtime_start_minutes,
        weekend_as_workday: form.weekend_as_workday,
        custom_workdays: form.custom_workdays
      });
      dialogVisible.value = false;
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = (row: AttendanceRuleItem) => {
  ElMessageBox.confirm(`确认删除规则【${row.name}】？`, "提示", { type: "warning" })
    .then(async () => {
      const res = await hrStore.removeAttendanceRule(row.id);
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

  .mx-2 {
    margin: 0 8px;
  }
}
</style>
