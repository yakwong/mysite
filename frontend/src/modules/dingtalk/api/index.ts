import { http } from "@/utils/http";

export interface DingTalkConfigForm {
  id: string;
  name: string;
  tenant_id: string;
  app_key: string;
  app_secret: string;
  agent_id: string;
  enabled: boolean;
  sync_users: boolean;
  sync_departments: boolean;
  sync_attendance: boolean;
  callback_url: string;
  callback_token: string;
  callback_aes_key: string;
  schedule: Record<string, any>;
  remark: string;
}

export interface DingTalkSyncInfo {
  status: string;
  message: string;
  lastSyncTime: string | null;
  lastDeptSyncTime: string | null;
  lastUserSyncTime: string | null;
  lastAttendanceSyncTime: string | null;
  deptCount: number;
  userCount: number;
  attendanceCount: number;
  accessTokenExpiresAt: string | null;
}

export interface DingTalkConfigResponse {
  success: boolean;
  data: DingTalkConfigForm[];
  msg: string;
  page?: number;
  limit?: number;
  total?: number;
}

export interface DingTalkLog {
  id: string;
  operation: string;
  operationLabel: string;
  status: string;
  statusLabel: string;
  level: string;
  message: string;
  detail: string;
  stats: Record<string, any>;
  retry_count: number;
  next_retry_at: string | null;
  create_time: string;
}

export interface DingTalkDepartment {
  dept_id: number;
  config_id: string;
  name: string;
  parent_id: number | null;
  order: number | null;
  leader_userid: string;
  dept_type: string;
  source_info: Record<string, any>;
  create_time: string;
  update_time: string;
}

export interface DingTalkUser {
  userid: string;
  config_id: string;
  name: string;
  mobile: string;
  email: string;
  active: boolean;
  job_number: string;
  title: string;
  dept_ids: number[];
  unionid: string;
  remark: string;
  source_info: Record<string, any>;
  create_time: string;
  update_time: string;
}

export interface DingTalkAttendanceRecord {
  record_id: string;
  config_id: string;
  userid: string;
  check_type: string;
  time_result: string;
  user_check_time: string;
  work_date: string | null;
  source_type: string;
  source_info: Record<string, any>;
  create_time: string;
  update_time: string;
}

export interface PaginationResponse<T> {
  success: boolean;
  data: T[];
  msg: string;
  page: number;
  limit: number;
  total: number;
}

export interface SyncCommandPayload {
  operation: "test_connection" | "sync_departments" | "sync_users" | "sync_attendance" | "full_sync";
  mode?: "full" | "incremental";
  start?: string;
  end?: string;
  userIds?: string[];
}

export const listConfigs = (params?: Record<string, any>) => http.request<DingTalkConfigResponse>("get", "/api/dingtalk/configs/", { params });

export const updateConfig = (id: string, data: Partial<DingTalkConfigForm>) => http.request<{ success: boolean; data: DingTalkConfigForm; msg: string }>("put", `/api/dingtalk/configs/${id}/`, { data });

export const createConfig = (data: Partial<DingTalkConfigForm>) => http.request<{ success: boolean; data: DingTalkConfigForm; msg: string }>("post", "/api/dingtalk/configs/", { data });

export const getSyncInfo = (id: string) => http.request<{ success: boolean; data: DingTalkSyncInfo; msg: string }>("get", `/api/dingtalk/configs/${id}/sync_info/`);

export const runSyncCommand = (data: SyncCommandPayload, configId?: string) => {
  const prefix = configId ? `/api/dingtalk/${configId}/sync/` : "/api/dingtalk/sync/";
  return http.request<{ success: boolean; data: any; msg: string }>("post", prefix, { data });
};

export const listLogs = (params?: Record<string, any>) => http.request<PaginationResponse<DingTalkLog>>("get", "/api/dingtalk/logs/", { params });

export const listDepartments = (params?: Record<string, any>) => http.request<PaginationResponse<DingTalkDepartment>>("get", "/api/dingtalk/departments/", { params });

export const listRemoteDepartments = (params: Record<string, any>) => http.request<{ success: boolean; data: Record<string, any>[]; msg: string; page: number; limit: number; total: number }>("get", "/api/dingtalk/departments/remote/", { params });

export const listUsers = (params?: Record<string, any>) => http.request<PaginationResponse<DingTalkUser>>("get", "/api/dingtalk/users/", { params });

export const listRemoteUsers = (params: Record<string, any>) => http.request<{ success: boolean; data: Record<string, any>[]; msg: string; page: number; limit: number; total: number }>("get", "/api/dingtalk/users/remote/", { params });

export const previewAttendance = (params: Record<string, any>) =>
  http.request<{ success: boolean; data: { records: DingTalkAttendanceRecord[]; count: number }; msg: string }>("get", "/api/dingtalk/attendances/remote/", { params });

export const listAttendance = (params?: Record<string, any>) => http.request<PaginationResponse<DingTalkAttendanceRecord>>("get", "/api/dingtalk/attendances/", { params });

export const listCursors = (params?: Record<string, any>) => http.request<PaginationResponse<{ cursor_type: string; value: string; extra: Record<string, any>; update_time: string }>>("get", "/api/dingtalk/cursors/", { params });
