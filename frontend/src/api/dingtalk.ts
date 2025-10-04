import { http } from "@/utils/http";

export interface DingTalkConfigForm {
  id: string;
  app_key: string;
  app_secret: string;
  agent_id: string;
  enabled: boolean;
  sync_users: boolean;
  sync_departments: boolean;
  callback_url: string;
  remark: string;
}

export interface DingTalkConfigResponse {
  success: boolean;
  data: {
    config: DingTalkConfigForm;
    syncInfo: DingTalkSyncInfo;
  };
  msg: string;
}

export interface DingTalkSyncInfo {
  status: string;
  message: string;
  lastSyncTime: string | null;
  lastDeptSyncTime: string | null;
  lastUserSyncTime: string | null;
  deptCount: number;
  userCount: number;
  accessTokenExpiresAt: string | null;
}

export interface DingTalkLogsResponse {
  success: boolean;
  data: DingTalkLog[];
  msg: string;
  page: number;
  limit: number;
  total: number;
}

export interface DingTalkLog {
  id: string;
  operation: string;
  operationLabel: string;
  status: string;
  statusLabel: string;
  message: string;
  detail: string;
  stats: Record<string, any>;
  create_time: string;
}

export interface DingTalkDepartment {
  dept_id: number;
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

export const getDingTalkConfig = () => http.request<DingTalkConfigResponse>("get", "/api/system/dingtalk/config/");

export const updateDingTalkConfig = (data: Partial<DingTalkConfigForm>) => http.request<DingTalkConfigResponse>("put", "/api/system/dingtalk/config/", { data });

export const getDingTalkSyncInfo = () => http.request<{ success: boolean; data: DingTalkSyncInfo; msg: string }>("get", "/api/system/dingtalk/sync/info/");

export const testDingTalkConnection = () => http.request<{ success: boolean; data: { accessToken: string; expiresAt: string | null }; msg: string }>("post", "/api/system/dingtalk/test-connection/");

export const syncDingTalkDepartments = () => http.request<{ success: boolean; data: { count: number }; msg: string }>("post", "/api/system/dingtalk/sync/departments/");

export const syncDingTalkUsers = () => http.request<{ success: boolean; data: { count: number }; msg: string }>("post", "/api/system/dingtalk/sync/users/");

export const syncDingTalkFull = () => http.request<{ success: boolean; data: { dept_count: number; user_count: number }; msg: string }>("post", "/api/system/dingtalk/sync/full/");

export const syncDingTalkAttendance = (data: { start: string; end: string }) => http.request<{ success: boolean; data: { count: number }; msg: string }>("post", "/api/system/dingtalk/sync/attendance/", { data });

export const getDingTalkLogs = (params?: Record<string, any>) => http.request<DingTalkLogsResponse>("get", "/api/system/dingtalk/logs/", { params });

export const getDingTalkDepartments = (params?: Record<string, any>) => http.request<{ success: boolean; data: DingTalkDepartment[]; msg: string; page: number; limit: number; total: number }>("get", "/api/system/dingtalk/departments/", { params });

export const getDingTalkUsers = (params?: Record<string, any>) => http.request<{ success: boolean; data: DingTalkUser[]; msg: string; page: number; limit: number; total: number }>("get", "/api/system/dingtalk/users/", { params });

export const getDingTalkAttendance = (params?: Record<string, any>) => http.request<{ success: boolean; data: any[]; msg: string; page: number; limit: number; total: number }>("get", "/api/system/dingtalk/attendances/", { params });
