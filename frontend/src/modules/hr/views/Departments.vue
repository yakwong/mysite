<template>
  <div class="page-container">
    <el-card shadow="never" class="mb-4">
      <el-form :inline="true" :model="search" label-width="80px" @submit.prevent>
        <el-form-item label="关键字">
          <el-input v-model="search.keyword" placeholder="部门名称/编码" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="search.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="启用" value="1" />
            <el-option label="停用" value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" :loading="loading" @click="handleImport">从钉钉导入</el-button>
          <el-button type="primary" plain @click="openDialog()">新增部门</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="deptList" border stripe :loading="loading">
        <el-table-column label="名称" prop="name" min-width="160" />
        <el-table-column label="编码" prop="code" min-width="120" />
        <el-table-column label="上级部门" prop="parentName" />
        <el-table-column label="状态" prop="status">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责人" prop="managerName" />
        <el-table-column label="更新时间" prop="update_time" min-width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-space>
              <el-button type="primary" text size="small" @click="openDialog(row)">编辑</el-button>
              <el-popconfirm title="确认删除该部门？" @confirm="handleDelete(row)">
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
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="50" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" maxlength="50" placeholder="唯一编码" />
        </el-form-item>
        <el-form-item label="上级部门">
          <el-select v-model="form.parent" placeholder="请选择" clearable filterable>
            <el-option v-for="dept in deptList" :key="dept.id" :label="dept.name" :value="dept.id" :disabled="dept.id === form.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="form.status" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="200" show-word-limit />
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
import type { HrDepartment } from "@/api/hr";

const hrStore = useHrStoreHook();
const search = reactive({ keyword: "", status: "" });
const formRef = ref<FormInstance>();
const dialogVisible = ref(false);
const submitLoading = ref(false);
const form = reactive({
  id: "",
  name: "",
  code: "",
  parent: "",
  status: true,
  description: ""
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入编码", trigger: "blur" }]
};

const loading = computed(() => hrStore.loading);
const deptList = computed(() => hrStore.departments);
const dialogTitle = computed(() => (form.id ? "编辑部门" : "新增部门"));

const handleSearch = async () => {
  await hrStore.fetchDepartments({ keyword: search.keyword, status: search.status });
};

const handleReset = async () => {
  search.keyword = "";
  search.status = "";
  await handleSearch();
};

const handleImport = async () => {
  await hrStore.importDepartments();
};

const openDialog = (row?: HrDepartment) => {
  if (row) {
    form.id = row.id;
    form.name = row.name;
    form.code = row.code;
    form.parent = row.parent ?? "";
    form.status = row.status === 1;
    form.description = row.description ?? "";
  } else {
    form.id = "";
    form.name = "";
    form.code = "";
    form.parent = "";
    form.status = true;
    form.description = "";
  }
  dialogVisible.value = true;
};

const handleSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async valid => {
    if (!valid) return;
    submitLoading.value = true;
    try {
      await hrStore.saveDepartment({
        id: form.id || undefined,
        name: form.name,
        code: form.code,
        parent: form.parent || null,
        status: form.status ? 1 : 0,
        description: form.description
      });
      dialogVisible.value = false;
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = (row: HrDepartment) => {
  ElMessageBox.confirm(`确认删除部门【${row.name}】？`, "提示", { type: "warning" })
    .then(async () => {
      const res = await hrStore.removeDepartment(row.id);
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
