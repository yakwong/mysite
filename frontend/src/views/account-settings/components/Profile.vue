<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import type { FormInstance, FormRules, UploadInstance, UploadFile } from "element-plus";
import { getMine, updateMine, uploadAvatar, type UserProfile } from "@/api/user";
import { message } from "@/utils/message";
import { deviceDetection, storageLocal } from "@pureadmin/utils";
import { useUserStoreHook } from "@/store/modules/user";
import { userKey } from "@/utils/auth";

const userStore = useUserStoreHook();

const userInfoFormRef = ref<FormInstance>();
const uploadRef = ref<UploadInstance>();
const loading = ref(false);
const uploading = ref(false);

const userInfos = reactive<UserProfile>({
  id: 0,
  avatar: "",
  username: "",
  nickname: "",
  email: "",
  phone: "",
  phone_verified: false,
  backup_email: null,
  description: ""
});

const rules: FormRules = {
  nickname: [{ required: true, message: "昵称必填", trigger: "blur" }],
  email: [{ required: true, message: "邮箱必填", trigger: "blur" }]
};

function updateCachedUser(payload: Partial<UserProfile>) {
  const cache = storageLocal().getItem<Record<string, any>>(userKey);
  if (cache) {
    storageLocal().setItem(userKey, { ...cache, ...payload });
  }
}

async function fetchProfile() {
  const { data } = await getMine();
  Object.assign(userInfos, data);
  userStore.SET_AVATAR(data.avatar ?? "");
  userStore.SET_NICKNAME(data.nickname ?? "");
  userStore.SET_EMAIL(data.email ?? "");
  updateCachedUser({ avatar: data.avatar, nickname: data.nickname, email: data.email });
}

async function handleAvatarChange(file: UploadFile) {
  if (!file.raw) return;
  uploading.value = true;
  const formData = new FormData();
  formData.append("file", file.raw);
  try {
    const { data } = await uploadAvatar(formData);
    Object.assign(userInfos, data);
    userStore.SET_AVATAR(data.avatar ?? "");
    updateCachedUser({ avatar: data.avatar });
    message("更新头像成功", { type: "success" });
  } catch (error) {
    message("更新头像失败", { type: "error" });
  } finally {
    uploadRef.value?.clearFiles();
    uploading.value = false;
  }
}

async function onSubmit(formEl?: FormInstance) {
  if (!formEl) return;
  await formEl.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      const payload = {
        nickname: userInfos.nickname,
        email: userInfos.email,
        phone: userInfos.phone,
        description: userInfos.description
      };
      const { data } = await updateMine(payload);
      Object.assign(userInfos, data);
      userStore.SET_NICKNAME(data.nickname ?? "");
      userStore.SET_EMAIL(data.email ?? "");
      updateCachedUser({
        nickname: data.nickname,
        email: data.email,
        phone: data.phone,
        description: data.description,
        backup_email: data.backup_email
      });
      message("更新信息成功", { type: "success" });
    } catch (error) {
      message("更新信息失败", { type: "error" });
    } finally {
      loading.value = false;
    }
  });
}

onMounted(() => {
  fetchProfile();
});
</script>

<template>
  <div :class="['min-w-[180px]', deviceDetection() ? 'max-w-[100%]' : 'max-w-[70%]']">
    <h3 class="my-8!">个人信息</h3>
    <el-form ref="userInfoFormRef" label-position="top" :rules="rules" :model="userInfos">
      <el-form-item label="头像">
        <el-avatar :size="80" :src="userInfos.avatar" />
        <el-upload ref="uploadRef" class="ml-4!" action="#" :limit="1" :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleAvatarChange">
          <el-button plain :loading="uploading">更新头像</el-button>
        </el-upload>
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="userInfos.username" disabled />
      </el-form-item>
      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="userInfos.nickname" placeholder="请输入昵称" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="userInfos.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="联系电话">
        <el-input v-model="userInfos.phone" placeholder="请输入联系电话" clearable />
      </el-form-item>
      <el-form-item label="简介">
        <el-input v-model="userInfos.description" placeholder="请输入简介" type="textarea" :autosize="{ minRows: 4, maxRows: 6 }" maxlength="120" show-word-limit />
      </el-form-item>
      <el-button type="primary" :loading="loading" @click="onSubmit(userInfoFormRef)"> 更新信息 </el-button>
    </el-form>
  </div>
</template>
