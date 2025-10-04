<template>
  <div class="maincontent">
    <!-- 钉钉API配置区域 -->
    <div class="config-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>钉钉API配置</span>
            <el-button type="primary" size="small" @click="handleSave">保存配置</el-button>
          </div>
        </template>

        <el-form ref="formRef" :model="configForm" label-width="140px" class="config-form">
          <el-form-item label="App Key：" prop="appKey">
            <el-input v-model="configForm.appKey" placeholder="请输入钉钉应用的App Key" clearable />
          </el-form-item>

          <el-form-item label="App Secret：" prop="appSecret">
            <el-input v-model="configForm.appSecret" type="password" placeholder="请输入钉钉应用的App Secret" clearable show-password />
          </el-form-item>

          <el-form-item label="Agent ID：" prop="agentId">
            <el-input v-model="configForm.agentId" placeholder="请输入钉钉应用的Agent ID" clearable />
          </el-form-item>

          <el-form-item label="启用状态：" prop="enabled">
            <el-switch v-model="configForm.enabled" active-text="已启用" inactive-text="已禁用" />
          </el-form-item>

          <el-form-item label="同步用户：" prop="syncUsers">
            <el-switch v-model="configForm.syncUsers" active-text="开启" inactive-text="关闭" />
          </el-form-item>

          <el-form-item label="同步部门：" prop="syncDepartments">
            <el-switch v-model="configForm.syncDepartments" active-text="开启" inactive-text="关闭" />
          </el-form-item>

          <el-form-item label="回调URL：" prop="callbackUrl">
            <el-input v-model="configForm.callbackUrl" placeholder="钉钉回调地址（选填）" clearable />
          </el-form-item>

          <el-form-item label="备注：" prop="remark">
            <el-input v-model="configForm.remark" type="textarea" :rows="3" placeholder="配置备注信息" />
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 同步操作区域 -->
    <div class="sync-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>数据同步</span>
          </div>
        </template>

        <div class="sync-buttons">
          <el-button type="primary" :icon="useRenderIcon('ri:user-line')" @click="handleSyncUsers">同步用户数据</el-button>
          <el-button type="primary" :icon="useRenderIcon('ri:building-line')" @click="handleSyncDepartments">同步部门数据</el-button>
          <el-button type="warning" :icon="useRenderIcon('ri:refresh-line')" @click="handleFullSync">全量同步</el-button>
          <el-button type="info" :icon="useRenderIcon('ri:history-line')" @click="handleViewLogs">查看同步日志</el-button>
        </div>

        <el-divider />

        <div class="sync-info">
          <el-descriptions title="同步信息" :column="2" border>
            <el-descriptions-item label="最后同步时间">{{ syncInfo.lastSyncTime || "暂无记录" }}</el-descriptions-item>
            <el-descriptions-item label="同步状态">
              <el-tag :type="syncInfo.status === 'success' ? 'success' : 'info'">{{ syncInfo.status === "success" ? "成功" : "未同步" }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="同步用户数">{{ syncInfo.userCount || 0 }}</el-descriptions-item>
            <el-descriptions-item label="同步部门数">{{ syncInfo.deptCount || 0 }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>
    </div>

    <!-- API测试区域 -->
    <div class="test-section">
      <el-card class="box-card">
        <template #header>
          <div class="card-header">
            <span>API连接测试</span>
          </div>
        </template>

        <div class="test-buttons">
          <el-button type="success" :icon="useRenderIcon('ri:link')" @click="handleTestConnection">测试连接</el-button>
          <el-button type="primary" :icon="useRenderIcon('ri:file-list-line')" @click="handleGetDeptList">获取部门列表</el-button>
          <el-button type="primary" :icon="useRenderIcon('ri:user-search-line')" @click="handleGetUserList">获取用户列表</el-button>
        </div>

        <el-divider />

        <div class="test-result">
          <el-input v-model="testResult" type="textarea" :rows="8" placeholder="测试结果将显示在这里..." readonly />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { message } from "@/utils/message";

defineOptions({
  name: "dingtalk"
});

const formRef = ref(null);

// 配置表单数据
const configForm = reactive({
  appKey: "",
  appSecret: "",
  agentId: "",
  enabled: false,
  syncUsers: true,
  syncDepartments: true,
  callbackUrl: "",
  remark: ""
});

// 同步信息
const syncInfo = ref({
  lastSyncTime: "",
  status: "",
  userCount: 0,
  deptCount: 0
});

// 测试结果
const testResult = ref("");

// 保存配置
function handleSave() {
  console.log("保存钉钉配置", configForm);
  message("配置保存成功（功能待实现）", { type: "success" });
}

// 同步用户数据
function handleSyncUsers() {
  console.log("同步用户数据");
  message("开始同步用户数据（功能待实现）", { type: "info" });
}

// 同步部门数据
function handleSyncDepartments() {
  console.log("同步部门数据");
  message("开始同步部门数据（功能待实现）", { type: "info" });
}

// 全量同步
function handleFullSync() {
  console.log("全量同步");
  message("开始全量同步（功能待实现）", { type: "info" });
}

// 查看同步日志
function handleViewLogs() {
  console.log("查看同步日志");
  message("查看同步日志（功能待实现）", { type: "info" });
}

// 测试连接
function handleTestConnection() {
  console.log("测试API连接");
  testResult.value = "正在测试连接...\n（功能待实现）";
}

// 获取部门列表
function handleGetDeptList() {
  console.log("获取钉钉部门列表");
  testResult.value = "正在获取部门列表...\n（功能待实现）";
}

// 获取用户列表
function handleGetUserList() {
  console.log("获取钉钉用户列表");
  testResult.value = "正在获取用户列表...\n（功能待实现）";
}

// 初始化加载配置
function loadConfig() {
  console.log("加载钉钉配置");
  // TODO: 从后端加载配置数据
}

onMounted(() => {
  loadConfig();
});
</script>

<style lang="scss" scoped>
.maincontent {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 141px);
  padding: 16px;
  overflow-y: auto;
}

.config-section,
.sync-section,
.test-section {
  .box-card {
    width: 100%;
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  span {
    font-size: 16px;
    font-weight: 600;
  }
}

.config-form {
  max-width: 800px;
}

.sync-buttons,
.test-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.sync-info {
  margin-top: 16px;
}

.test-result {
  margin-top: 16px;
}

::v-deep(.el-descriptions__label) {
  font-weight: 500;
}
</style>
