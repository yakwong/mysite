import { http } from "@/utils/http";

export type ApiResponse<T> = {
  success: boolean;
  data: T;
  msg: string;
};

export type UserResult = {
  success: boolean;
  data: {
    avatar: string;
    /** 用户名 */
    username: string;
    /** 昵称 */
    nickname: string;
    /** 当前登录用户的角色 */
    roles: Array<string>;
    /** 按钮级别权限 */
    permissions: Array<string>;
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（格式'xxxx/xx/xx xx:xx:xx'） */
    expires: Date;
  };
  msg: string;
};

export interface UserProfile {
  id: number;
  avatar: string | null;
  username: string;
  nickname: string | null;
  email: string;
  phone: string | null;
  phone_verified: boolean;
  backup_email: string | null;
  description: string | null;
  password_strength?: string | null;
  password_updated_at?: string | null;
  security_question?: string | null;
  security_question_updated_at?: string | null;
  two_factor_enabled?: boolean;
  login_notifier_enabled?: boolean;
}

export type UserProfileResult = {
  success: boolean;
  data: UserProfile;
  msg: string;
};

export interface SecurityState {
  password_strength: string;
  password_updated_at: string | null;
  phone: string | null;
  phone_verified: boolean;
  masked_phone: string | null;
  backup_email: string | null;
  masked_backup_email: string | null;
  security_question: string | null;
  security_question_set: boolean;
  security_question_updated_at: string | null;
  two_factor_enabled: boolean;
  login_notifier_enabled: boolean;
}

export type SecurityStateResult = ApiResponse<SecurityState>;

export interface SecurityLogItem {
  id: number;
  summary: string;
  ip: string;
  address: string;
  system: string;
  browser: string;
  operating_time: string;
  status: boolean;
}

export type SecurityLogResult = {
  success: boolean;
  data: {
    list: SecurityLogItem[];
    total: number;
    pageSize: number;
    currentPage: number;
  };
  msg: string;
};

export type UserListResult = {
  success: boolean;
  data: Array<object>;
  msg: string;
  total: number;
  page: number;
  limit: number;
};

export type RefreshTokenResult = {
  success: boolean;
  data: {
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（格式'xxxx/xx/xx xx:xx:xx'） */
    expires: Date;
  };
  msg: string;
};

/** 登录 */
export const getLogin = (data?: object) => {
  return http.request<UserResult>("post", "/api/user/login/", { data });
};

/** 刷新`token` */
export const refreshTokenApi = (data?: object) => {
  return http.request<RefreshTokenResult>("post", "/api/token/refresh/", {
    data
  });
};

/** 获取用户数据列表 */
export const getUserList = (params?: object) => {
  return http.request<UserListResult>("get", "/api/user/", { params });
};

/** 更新用户数据 */
export const patchUser = (id?: number, data?: object) => {
  return http.request<UserResult>("patch", "/api/user/" + id + "/", { data });
};

/** 新增用户数据 */
export const postUser = (data?: object) => {
  return http.request<UserResult>("post", "/api/user/", { data });
};

/** 删除用户数据 */
export const deleteUser = (id?: number) => {
  return http.request<UserResult>("delete", "/api/user/" + id + "/");
};

/** 获取个人信息 */
export const getMine = () => {
  return http.request<UserProfileResult>("get", "/api/user/profile/");
};

/** 更新个人信息 */
export const updateMine = (data?: Partial<UserProfile>) => {
  return http.request<UserProfileResult>("patch", "/api/user/profile/", { data });
};

/** 上传头像 */
export const uploadAvatar = (data: FormData) => {
  return http.request<UserProfileResult>("post", "/api/user/profile/avatar/", {
    data,
    headers: { "Content-Type": "multipart/form-data" }
  });
};

/** 获取安全日志 */
export const getSecurityLogs = (params?: { page?: number; limit?: number }) => {
  return http.request<SecurityLogResult>("get", "/api/user/security-logs/", { params });
};

/** 获取账户安全概览 */
export const getSecurityState = () => {
  return http.request<SecurityStateResult>("get", "/api/user/profile/security-state/");
};

/** 发送安全验证码 */
export const sendSecurityCode = (data: { action: "bind_phone" | "unbind_phone" | "backup_email"; target?: string }) => {
  return http.request<ApiResponse<{ expires_in: number; code?: string }>>("post", "/api/user/profile/send-code/", { data });
};

/** 修改密码 */
export const changePassword = (data: { old_password: string; new_password: string; confirm_password: string }) => {
  return http.request<ApiResponse<{ password_strength: string; password_updated_at: string | null }>>("post", "/api/user/profile/change-password/", { data });
};

/** 绑定手机号 */
export const bindPhone = (data: { phone: string; code: string }) => {
  return http.request<ApiResponse<{ phone: string | null; phone_verified: boolean; masked_phone: string | null }>>("post", "/api/user/profile/bind-phone/", { data });
};

/** 解绑手机号 */
export const unbindPhone = (data: { code: string }) => {
  return http.request<ApiResponse<{ phone: string | null; phone_verified: boolean; masked_phone: string | null }>>("post", "/api/user/profile/unbind-phone/", { data });
};

/** 设置备用邮箱 */
export const setBackupEmail = (data: { backup_email: string; code: string }) => {
  return http.request<ApiResponse<{ backup_email: string | null; masked_backup_email: string | null }>>("post", "/api/user/profile/backup-email/", { data });
};

/** 移除备用邮箱 */
export const removeBackupEmail = () => {
  return http.request<ApiResponse<{ backup_email: string | null }>>("delete", "/api/user/profile/backup-email/");
};

/** 设置密保问题 */
export const setSecurityQuestion = (data: { question: string; answer: string; current_answer?: string }) => {
  return http.request<ApiResponse<{ security_question: string | null; security_question_updated_at: string | null; security_question_set: boolean }>>("post", "/api/user/profile/security-question/", { data });
};

/** 清除密保问题 */
export const clearSecurityQuestion = () => {
  return http.request<ApiResponse<{ security_question_set: boolean }>>("delete", "/api/user/profile/security-question/");
};

/** 设置两步验证 */
export const toggleTwoFactor = (data: { enabled: boolean }) => {
  return http.request<ApiResponse<{ two_factor_enabled: boolean }>>("post", "/api/user/profile/two-factor/", { data });
};

/** 设置登录提醒 */
export const toggleLoginNotifier = (data: { enabled: boolean }) => {
  return http.request<ApiResponse<{ login_notifier_enabled: boolean }>>("post", "/api/user/profile/login-notifier/", { data });
};
