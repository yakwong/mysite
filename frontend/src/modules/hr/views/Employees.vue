<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-4">
      <el-form :inline="true" :model="search" label-width="80px" @submit.prevent>
        <el-form-item label="关键字">
          <el-input v-model="search.keyword" placeholder="姓名/工号" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="search.department" placeholder="全部" clearable filterable style="width: 180px">
            <el-option v-for="dept in deptList" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="search.status" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" :loading="loading" @click="handleImport">从钉钉导入</el-button>
          <el-button type="primary" plain @click="openDialog()">新增员工</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="employeeList" border stripe :loading="loading">
        <el-table-column label="姓名" prop="name" min-width="120" />
        <el-table-column label="工号" prop="job_number" min-width="120" />
        <el-table-column label="部门" prop="departmentName" />
        <el-table-column label="职位" prop="title" />
        <el-table-column label="类型" prop="employmentTypeLabel" />
        <el-table-column label="状态" prop="employmentStatusLabel">
          <template #default="{ row }">
            <el-tag :type="row.employment_status === 4 ? 'info' : 'success'">{{ row.employmentStatusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="邮箱" prop="email" min-width="160" />
        <el-table-column label="电话" prop="phone" min-width="140" />
        <el-table-column label="基础工资" prop="base_salary" min-width="120" />
        <el-table-column label="固定补贴" prop="allowance" min-width="120" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-space>
              <el-button type="primary" text size="small" @click="openDialog(row)">编辑</el-button>
              <el-popconfirm title="确认删除该员工？" @confirm="handleDelete(row)">
                <template #reference>
                  <el-button type="danger" text size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="工号" prop="job_number">
            <el-input v-model="form.job_number" placeholder="唯一工号" />
          </el-form-item>
          <el-form-item label="部门">
            <el-select v-model="form.department" placeholder="请选择" clearable filterable>
              <el-option v-for="dept in deptList" :key="dept.id" :label="dept.name" :value="dept.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="职位">
            <el-input v-model="form.title" placeholder="职位名称" />
          </el-form-item>
          <el-form-item label="雇佣类型" prop="employment_type">
            <el-select v-model="form.employment_type" placeholder="请选择">
              <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="雇佣状态" prop="employment_status">
            <el-select v-model="form.employment_status" placeholder="请选择">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="入职日期">
            <el-date-picker v-model="form.hire_date" type="date" placeholder="选择日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="转正日期">
            <el-date-picker v-model="form.regular_date" type="date" placeholder="选择日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="离职日期">
            <el-date-picker v-model="form.separation_date" type="date" placeholder="选择日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="邮箱" />
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="form.phone" placeholder="手机号" />
          </el-form-item>
          <el-form-item label="基础工资" prop="base_salary">
            <el-input-number v-model="form.base_salary" :min="0" :precision="2" :step="100" controls-position="right" />
          </el-form-item>
          <el-form-item label="固定补贴">
            <el-input-number v-model="form.allowance" :min="0" :precision="2" :step="50" controls-position="right" />
          </el-form-item>
        </div>
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
import type { HrEmployee } from "@/api/hr";

const hrStore = useHrStoreHook();
const search = reactive({ keyword: "", department: "", status: "" });
const formRef = ref<FormInstance>();
const dialogVisible = ref(false);
const submitLoading = ref(false);

const form = reactive({
  id: "",
  name: "",
  job_number: "",
  department: "",
  title: "",
  employment_type: 1,
  employment_status: 2,
  hire_date: "",
  regular_date: "",
  separation_date: "",
  email: "",
  phone: "",
  base_salary: 0,
  allowance: 0
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  job_number: [{ required: true, message: "请输入工号", trigger: "blur" }],
  employment_type: [{ required: true, message: "请选择类型", trigger: "change" }],
  employment_status: [{ required: true, message: "请选择状态", trigger: "change" }],
  base_salary: [{ required: true, message: "请输入基础工资", trigger: "change" }]
};

const statusOptions = [
  { value: 1, label: "试用" },
  { value: 2, label: "在职" },
  { value: 3, label: "停薪留职" },
  { value: 4, label: "离职" }
];

const typeOptions = [
  { value: 1, label: "全职" },
  { value: 2, label: "兼职" },
  { value: 3, label: "实习" },
  { value: 4, label: "外包" }
];

const loading = computed(() => hrStore.loading);
const deptList = computed(() => hrStore.departments);
const employeeList = computed(() => hrStore.employees);
const dialogTitle = computed(() => (form.id ? "编辑员工" : "新增员工"));

const handleSearch = async () => {
  await hrStore.fetchDepartments();
  await hrStore.fetchEmployees({
    keyword: search.keyword,
    department: search.department,
    status: search.status
  });
};

const handleReset = async () => {
  search.keyword = "";
  search.department = "";
  search.status = "";
  await handleSearch();
};

const handleImport = async () => {
  await hrStore.importEmployees();
};

const openDialog = (row?: HrEmployee) => {
  if (row) {
    form.id = row.id;
    form.name = row.name;
    form.job_number = row.job_number;
    form.department = row.department ?? "";
    form.title = row.title ?? "";
    form.employment_type = row.employment_type;
    form.employment_status = row.employment_status;
    form.hire_date = row.hire_date ?? "";
    form.regular_date = row.regular_date ?? "";
    form.separation_date = row.separation_date ?? "";
    form.email = row.email ?? "";
    form.phone = row.phone ?? "";
    form.base_salary = Number(row.base_salary ?? 0);
    form.allowance = Number(row.allowance ?? 0);
  } else {
    form.id = "";
    form.name = "";
    form.job_number = "";
    form.department = search.department || "";
    form.title = "";
    form.employment_type = 1;
    form.employment_status = 2;
    form.hire_date = "";
    form.regular_date = "";
    form.separation_date = "";
    form.email = "";
    form.phone = "";
    form.base_salary = 0;
    form.allowance = 0;
  }
  dialogVisible.value = true;
};

const handleSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async valid => {
    if (!valid) return;
    submitLoading.value = true;
    try {
      await hrStore.saveEmployee({
        id: form.id || undefined,
        name: form.name,
        job_number: form.job_number,
        department: form.department || null,
        title: form.title,
        employment_type: form.employment_type,
        employment_status: form.employment_status,
        hire_date: form.hire_date || null,
        regular_date: form.regular_date || null,
        separation_date: form.separation_date || null,
        email: form.email,
        phone: form.phone,
        base_salary: form.base_salary,
        allowance: form.allowance
      });
      dialogVisible.value = false;
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = (row: HrEmployee) => {
  ElMessageBox.confirm(`确认删除员工【${row.name}】？`, "提示", { type: "warning" })
    .then(async () => {
      const res = await hrStore.removeEmployee(row.id);
      if (!res.success) {
        ElMessage.error(res.msg);
      }
    })
    .catch(() => {
      /* ignore */
    });
};

handleSearch();
</script>

<style scoped lang="scss">
.page-container {
  padding: 16px;

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
