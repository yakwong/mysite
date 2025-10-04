<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import dayjs from "dayjs";
import { ElMessageBox } from "element-plus";
import { deviceDetection } from "@pureadmin/utils";
import { message } from "@/utils/message";
import { bindPhone, changePassword, clearSecurityQuestion, getSecurityState, removeBackupEmail, sendSecurityCode, setBackupEmail, setSecurityQuestion, toggleLoginNotifier, toggleTwoFactor, type SecurityState, unbindPhone } from "@/api/user";

defineOptions({
  name: "AccountManagement"
});

const loading = ref(true);
const overview = ref<SecurityState | null>(null);

const dialogs = reactive({
  password: false,
  phone: false,
  unbindPhone: false,
  backupEmail: false,
  securityQuestion: false
});

const passwordFormRef = ref<FormInstance>();
const passwordForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: ""
});
const passwordLoading = ref(false);

const phoneFormRef = ref<FormInstance>();
const phoneForm = reactive({
  phone: "",
  code: ""
});
const bindPhoneLoading = ref(false);

const unbindFormRef = ref<FormInstance>();
const unbindForm = reactive({
  code: ""
});
const unbindLoading = ref(false);

const backupEmailFormRef = ref<FormInstance>();
const backupEmailForm = reactive({
  backup_email: "",
  code: ""
});
const backupEmailLoading = ref(false);

const securityQuestionFormRef = ref<FormInstance>();
const securityQuestionForm = reactive({
  question: "",
  answer: "",
  current_answer: ""
});
const securityQuestionLoading = ref(false);

const sendingCode = reactive({
  bindPhone: false,
  unbindPhone: false,
  backupEmail: false
});
const countdown = reactive({
  bindPhone: 0,
  unbindPhone: 0,
  backupEmail: 0
});
const countdownTimers: Record<keyof typeof countdown, number | null> = {
  bindPhone: null,
  unbindPhone: null,
  backupEmail: null
};

const twoFactorLoading = ref(false);
const loginNotifierLoading = ref(false);

const passwordRules: FormRules = {
  old_password: [{ required: true, message: "请输入当前密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    {
      validator: (_, value: string, callback) => {
        if (!value) return callback();
        const lengthOk = value.length >= 8;
        const mixCount = [/[A-Z]/, /[a-z]/, /\d/, /[^A-Za-z0-9]/].filter(pattern => pattern.test(value)).length;
        if (!lengthOk || mixCount < 3) {
          callback(new Error("至少包含8位且使用大小写、数字、符号3种组合"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ],
  confirm_password: [
    { required: true, message: "请再次输入新密码", trigger: "blur" },
    {
      validator: (_, value: string, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};

const phoneRules: FormRules = {
  phone: [
    { required: true, message: "请输入手机号", trigger: "blur" },
    { pattern: /^1[3-9]\d{9}$/, message: "请输入有效的中国大陆手机号", trigger: "blur" }
  ],
  code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
};

const unbindRules: FormRules = {
  code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
};

const backupEmailRules: FormRules = {
  backup_email: [{ required: true, message: "请输入邮箱", trigger: "blur" }],
  code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
};

const securityQuestionRules: FormRules = {
  question: [{ required: true, message: "请输入密保问题", trigger: "blur" }],
  answer: [{ required: true, message: "请输入密保答案", trigger: "blur" }],
  current_answer: [
    {
      validator: (_, value: string, callback) => {
        if (overview.value?.security_question_set && !value) {
          callback(new Error("请先输入当前密保答案"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};

type ManagementItem = {
  key: string;
  title: string;
  illustrate: string;
  primaryText: string;
  onPrimary: () => void;
  loading?: boolean;
  disabled?: boolean;
  secondaryText?: string;
  onSecondary?: () => void;
  secondaryLoading?: boolean;
};

const strengthLabel: Record<string, string> = {
  strong: "强",
  medium: "中",
  weak: "弱",
  unknown: "未知"
};

function formatTime(value: string | null | undefined) {
  if (!value) return "";
  return dayjs(value).format("YYYY-MM-DD HH:mm");
}

const managementItems = computed<ManagementItem[]>(() => {
  const state = overview.value;
  const items: ManagementItem[] = [];
  items.push({
    key: "password",
    title: "账户密码",
    illustrate: state ? `当前密码强度：${strengthLabel[state.password_strength] ?? "未知"}${state.password_updated_at ? `，上次修改时间：${formatTime(state.password_updated_at)}` : "，建议定期更新密码"}` : "正在获取密码信息...",
    primaryText: "修改",
    onPrimary: openPasswordDialog
  });

  items.push({
    key: "phone",
    title: "密保手机",
    illustrate: state ? (state.phone_verified && state.masked_phone ? `已绑定手机：${state.masked_phone}` : "未绑定密保手机，建议绑定用于找回密码和异常登录验证") : "正在获取手机信息...",
    primaryText: state?.phone_verified ? "更换" : "绑定",
    onPrimary: openPhoneDialog,
    secondaryText: state?.phone_verified ? "解绑" : undefined,
    onSecondary: state?.phone_verified ? openUnbindPhoneDialog : undefined
  });

  items.push({
    key: "securityQuestion",
    title: "密保问题",
    illustrate: state ? (state.security_question_set && state.security_question ? `已设置密保问题：${state.security_question}` : "未设置密保问题，建议设置以提升找回密码成功率") : "正在获取密保信息...",
    primaryText: state?.security_question_set ? "修改" : "设置",
    onPrimary: openSecurityQuestionDialog,
    secondaryText: state?.security_question_set ? "清除" : undefined,
    onSecondary: state?.security_question_set ? handleClearSecurityQuestion : undefined,
    secondaryLoading: securityQuestionLoading.value
  });

  items.push({
    key: "backupEmail",
    title: "备用邮箱",
    illustrate: state ? (state.backup_email && state.masked_backup_email ? `已绑定备用邮箱：${state.masked_backup_email}` : "未绑定备用邮箱，绑定后可在忘记密码时接收验证码") : "正在获取邮箱信息...",
    primaryText: state?.backup_email ? "更换" : "绑定",
    onPrimary: openBackupEmailDialog,
    secondaryText: state?.backup_email ? "解除绑定" : undefined,
    onSecondary: state?.backup_email ? handleRemoveBackupEmail : undefined
  });

  items.push({
    key: "loginNotifier",
    title: "登录提醒",
    illustrate: state ? (state.login_notifier_enabled ? "已开启登录提醒，新的登录将同步通知" : "未开启登录提醒，建议开启以掌握账户动态") : "正在获取登录提醒状态...",
    primaryText: state?.login_notifier_enabled ? "关闭" : "开启",
    onPrimary: handleToggleLoginNotifier,
    loading: loginNotifierLoading.value,
    disabled: !state
  });

  items.push({
    key: "twoFactor",
    title: "两步验证",
    illustrate: state ? (state.two_factor_enabled ? "已开启两步验证，登录需额外验证身份" : "未开启两步验证，建议开启增强账户安全") : "正在获取两步验证状态...",
    primaryText: state?.two_factor_enabled ? "关闭" : "开启",
    onPrimary: handleToggleTwoFactor,
    loading: twoFactorLoading.value,
    disabled: !state
  });

  return items;
});

async function fetchSecurityState() {
  loading.value = true;
  try {
    const { data } = await getSecurityState();
    overview.value = data;
  } finally {
    loading.value = false;
  }
}

function resetPasswordDialog() {
  passwordForm.old_password = "";
  passwordForm.new_password = "";
  passwordForm.confirm_password = "";
  nextTick(() => passwordFormRef.value?.clearValidate());
}

function openPasswordDialog() {
  resetPasswordDialog();
  dialogs.password = true;
}

async function handlePasswordSubmit() {
  if (!passwordFormRef.value) return;
  try {
    await passwordFormRef.value.validate();
  } catch (error) {
    return;
  }
  passwordLoading.value = true;
  try {
    await changePassword({ ...passwordForm });
    message("密码修改成功", { type: "success" });
    dialogs.password = false;
    await fetchSecurityState();
  } finally {
    passwordLoading.value = false;
  }
}

function resetPhoneDialog() {
  phoneForm.phone = overview.value?.phone ?? "";
  phoneForm.code = "";
  nextTick(() => phoneFormRef.value?.clearValidate());
}

function openPhoneDialog() {
  resetPhoneDialog();
  dialogs.phone = true;
}

function openUnbindPhoneDialog() {
  if (!overview.value?.phone_verified) {
    message("当前未绑定手机号", { type: "info" });
    return;
  }
  unbindForm.code = "";
  nextTick(() => unbindFormRef.value?.clearValidate());
  dialogs.unbindPhone = true;
}

function resetBackupEmailDialog() {
  backupEmailForm.backup_email = overview.value?.backup_email ?? "";
  backupEmailForm.code = "";
  nextTick(() => backupEmailFormRef.value?.clearValidate());
}

function openBackupEmailDialog() {
  resetBackupEmailDialog();
  dialogs.backupEmail = true;
}

function openSecurityQuestionDialog() {
  securityQuestionForm.question = overview.value?.security_question ?? "";
  securityQuestionForm.answer = "";
  securityQuestionForm.current_answer = "";
  nextTick(() => securityQuestionFormRef.value?.clearValidate());
  dialogs.securityQuestion = true;
}

type CodeAction = "bindPhone" | "unbindPhone" | "backupEmail";
const actionMap: Record<CodeAction, "bind_phone" | "unbind_phone" | "backup_email"> = {
  bindPhone: "bind_phone",
  unbindPhone: "unbind_phone",
  backupEmail: "backup_email"
};

function startCountdown(key: CodeAction, seconds = 60) {
  countdown[key] = seconds;
  if (countdownTimers[key]) {
    window.clearInterval(countdownTimers[key]!);
  }
  countdownTimers[key] = window.setInterval(() => {
    if (countdown[key] <= 1) {
      window.clearInterval(countdownTimers[key]!);
      countdownTimers[key] = null;
      countdown[key] = 0;
    } else {
      countdown[key] -= 1;
    }
  }, 1000);
}

async function handleSendCode(type: CodeAction) {
  if (sendingCode[type]) return;
  if (type === "bindPhone") {
    try {
      await phoneFormRef.value?.validateField("phone");
    } catch (error) {
      return;
    }
  }
  if (type === "backupEmail") {
    try {
      await backupEmailFormRef.value?.validateField("backup_email");
    } catch (error) {
      return;
    }
  }
  if (type === "unbindPhone" && !overview.value?.phone_verified) {
    message("当前未绑定手机号", { type: "info" });
    return;
  }
  sendingCode[type] = true;
  try {
    const target = type === "bindPhone" ? phoneForm.phone : type === "backupEmail" ? backupEmailForm.backup_email : undefined;
    const { data } = await sendSecurityCode({ action: actionMap[type], target });
    const hint = data.code ? `（测试环境验证码：${data.code}）` : "";
    message(`验证码已发送${hint}`, { type: "success" });
    startCountdown(type);
  } finally {
    sendingCode[type] = false;
  }
}

async function handleBindPhoneSubmit() {
  if (!phoneFormRef.value) return;
  try {
    await phoneFormRef.value.validate();
  } catch (error) {
    return;
  }
  bindPhoneLoading.value = true;
  try {
    await bindPhone({ ...phoneForm });
    message("绑定手机号成功", { type: "success" });
    dialogs.phone = false;
    await fetchSecurityState();
  } finally {
    bindPhoneLoading.value = false;
  }
}

async function handleUnbindPhoneSubmit() {
  if (!unbindFormRef.value) return;
  try {
    await unbindFormRef.value.validate();
  } catch (error) {
    return;
  }
  unbindLoading.value = true;
  try {
    await unbindPhone({ ...unbindForm });
    message("解绑手机号成功", { type: "success" });
    dialogs.unbindPhone = false;
    await fetchSecurityState();
  } finally {
    unbindLoading.value = false;
  }
}

async function handleBackupEmailSubmit() {
  if (!backupEmailFormRef.value) return;
  try {
    await backupEmailFormRef.value.validate();
  } catch (error) {
    return;
  }
  backupEmailLoading.value = true;
  try {
    await setBackupEmail({ ...backupEmailForm });
    message("备用邮箱设置成功", { type: "success" });
    dialogs.backupEmail = false;
    await fetchSecurityState();
  } finally {
    backupEmailLoading.value = false;
  }
}

async function handleRemoveBackupEmail() {
  if (!overview.value?.backup_email) return;
  try {
    await ElMessageBox.confirm("确定解除备用邮箱绑定吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
  } catch (error) {
    return;
  }
  await removeBackupEmail();
  message("已解除备用邮箱", { type: "success" });
  await fetchSecurityState();
}

async function handleSecurityQuestionSubmit() {
  if (!securityQuestionFormRef.value) return;
  try {
    await securityQuestionFormRef.value.validate();
  } catch (error) {
    return;
  }
  securityQuestionLoading.value = true;
  try {
    await setSecurityQuestion({ ...securityQuestionForm });
    message("密保问题设置成功", { type: "success" });
    dialogs.securityQuestion = false;
    await fetchSecurityState();
  } finally {
    securityQuestionLoading.value = false;
  }
}

async function handleClearSecurityQuestion() {
  securityQuestionLoading.value = true;
  try {
    await clearSecurityQuestion();
    message("已清除密保问题", { type: "success" });
    await fetchSecurityState();
  } finally {
    securityQuestionLoading.value = false;
  }
}

async function handleToggleLoginNotifier() {
  if (!overview.value) return;
  loginNotifierLoading.value = true;
  const enabled = !overview.value.login_notifier_enabled;
  try {
    const { data } = await toggleLoginNotifier({ enabled });
    overview.value = overview.value ? { ...overview.value, login_notifier_enabled: data.login_notifier_enabled } : overview.value;
    message(enabled ? "已开启登录提醒" : "已关闭登录提醒", { type: "success" });
  } finally {
    loginNotifierLoading.value = false;
  }
}

async function handleToggleTwoFactor() {
  if (!overview.value) return;
  twoFactorLoading.value = true;
  try {
    await toggleTwoFactor({ enabled: !overview.value.two_factor_enabled });
    message("两步验证设置已更新", { type: "success" });
    await fetchSecurityState();
  } finally {
    twoFactorLoading.value = false;
  }
}

onMounted(() => {
  fetchSecurityState();
});

onBeforeUnmount(() => {
  (Object.keys(countdownTimers) as CodeAction[]).forEach(key => {
    if (countdownTimers[key]) {
      window.clearInterval(countdownTimers[key]!);
      countdownTimers[key] = null;
    }
  });
});
</script>

<template>
  <div :class="['min-w-[180px]', deviceDetection() ? 'max-w-[100%]' : 'max-w-[70%]']">
    <h3 class="my-8!">账户管理</h3>
    <el-skeleton v-if="loading" animated :count="4">
      <template #template>
        <div class="py-4">
          <el-skeleton-item variant="text" style="width: 40%" />
          <el-skeleton-item variant="text" style="width: 70%; margin-top: 12px" />
        </div>
      </template>
    </el-skeleton>
    <template v-else>
      <div v-for="item in managementItems" :key="item.key">
        <div class="flex items-center">
          <div class="flex-1">
            <p class="font-semibold">{{ item.title }}</p>
            <el-text class="mx-1" type="info">{{ item.illustrate }}</el-text>
          </div>
          <div class="flex items-center gap-2">
            <el-button type="primary" text :loading="item.loading" :disabled="item.disabled" @click="item.onPrimary">
              {{ item.primaryText }}
            </el-button>
            <el-button v-if="item.secondaryText" text type="danger" :loading="item.secondaryLoading" @click="item.onSecondary">
              {{ item.secondaryText }}
            </el-button>
          </div>
        </div>
        <el-divider />
      </div>
    </template>
  </div>

  <el-dialog v-model="dialogs.password" title="修改账户密码" width="460px" @closed="resetPasswordDialog">
    <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top">
      <el-form-item label="当前密码" prop="old_password">
        <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入当前密码" />
      </el-form-item>
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码" />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm_password">
        <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogs.password = false">取消</el-button>
      <el-button type="primary" :loading="passwordLoading" @click="handlePasswordSubmit">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="dialogs.phone" title="绑定/更换密保手机" width="460px" @closed="resetPhoneDialog">
    <el-form ref="phoneFormRef" :model="phoneForm" :rules="phoneRules" label-position="top">
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="phoneForm.phone" placeholder="请输入要绑定的手机号" />
      </el-form-item>
      <el-form-item label="验证码" prop="code">
        <div class="flex items-center gap-2 w-full">
          <el-input v-model="phoneForm.code" placeholder="请输入验证码" class="flex-1" />
          <el-button type="primary" plain :loading="sendingCode.bindPhone" :disabled="countdown.bindPhone > 0" @click="handleSendCode('bindPhone')">
            {{ countdown.bindPhone > 0 ? `重新发送(${countdown.bindPhone}s)` : "发送验证码" }}
          </el-button>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogs.phone = false">取消</el-button>
      <el-button type="primary" :loading="bindPhoneLoading" @click="handleBindPhoneSubmit">提交</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="dialogs.unbindPhone" title="解绑密保手机" width="420px">
    <el-form ref="unbindFormRef" :model="unbindForm" :rules="unbindRules" label-position="top">
      <el-form-item label="验证码" prop="code">
        <div class="flex items-center gap-2 w-full">
          <el-input v-model="unbindForm.code" placeholder="请输入验证码" class="flex-1" />
          <el-button type="primary" plain :loading="sendingCode.unbindPhone" :disabled="countdown.unbindPhone > 0" @click="handleSendCode('unbindPhone')">
            {{ countdown.unbindPhone > 0 ? `重新发送(${countdown.unbindPhone}s)` : "发送验证码" }}
          </el-button>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogs.unbindPhone = false">取消</el-button>
      <el-button type="danger" :loading="unbindLoading" @click="handleUnbindPhoneSubmit">确认解绑</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="dialogs.backupEmail" title="绑定备用邮箱" width="460px" @closed="resetBackupEmailDialog">
    <el-form ref="backupEmailFormRef" :model="backupEmailForm" :rules="backupEmailRules" label-position="top">
      <el-form-item label="备用邮箱" prop="backup_email">
        <el-input v-model="backupEmailForm.backup_email" placeholder="请输入备用邮箱" />
      </el-form-item>
      <el-form-item label="验证码" prop="code">
        <div class="flex items-center gap-2 w-full">
          <el-input v-model="backupEmailForm.code" placeholder="请输入验证码" class="flex-1" />
          <el-button type="primary" plain :loading="sendingCode.backupEmail" :disabled="countdown.backupEmail > 0" @click="handleSendCode('backupEmail')">
            {{ countdown.backupEmail > 0 ? `重新发送(${countdown.backupEmail}s)` : "发送验证码" }}
          </el-button>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogs.backupEmail = false">取消</el-button>
      <el-button type="primary" :loading="backupEmailLoading" @click="handleBackupEmailSubmit">提交</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="dialogs.securityQuestion" title="设置密保问题" width="460px">
    <el-form ref="securityQuestionFormRef" :model="securityQuestionForm" :rules="securityQuestionRules" label-position="top">
      <el-form-item label="密保问题" prop="question">
        <el-input v-model="securityQuestionForm.question" placeholder="请输入密保问题" />
      </el-form-item>
      <el-form-item label="密保答案" prop="answer">
        <el-input v-model="securityQuestionForm.answer" placeholder="请输入密保答案" type="password" show-password />
      </el-form-item>
      <el-form-item v-if="overview?.security_question_set" label="当前密保答案" prop="current_answer">
        <el-input v-model="securityQuestionForm.current_answer" placeholder="请输入当前密保答案" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogs.securityQuestion = false">取消</el-button>
      <el-button type="primary" :loading="securityQuestionLoading" @click="handleSecurityQuestionSubmit"> 保存 </el-button>
    </template>
  </el-dialog>
</template>

<style lang="scss" scoped>
.el-divider--horizontal {
  border-top: 0.1px var(--el-border-color) var(--el-border-style);
}
</style>
