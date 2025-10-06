import { http } from "@/utils/http";

export interface HrApiResponse<T> {
  success: boolean;
  data: T;
  msg: string;
  page?: number;
  limit?: number;
  total?: number;
}

export interface HrDepartment {
  id: string;
  name: string;
  code: string;
  config_id: string;
  status: number;
  statusLabel: string;
  description: string;
  metadata: Record<string, any>;
  parent: string | null;
  parentName: string | null;
  manager: string | null;
  managerName: string | null;
  ding_department: number | null;
  dingDeptId: string | null;
  create_time: string;
  update_time: string;
}

export interface HrEmployee {
  id: string;
  name: string;
  job_number: string;
  config_id: string;
  email: string;
  phone: string;
  title: string;
  employment_type: number;
  employmentTypeLabel: string;
  employment_status: number;
  employmentStatusLabel: string;
  hire_date: string | null;
  regular_date: string | null;
  separation_date: string | null;
  base_salary: string | number;
  allowance: string | number;
  metadata: Record<string, any>;
  department: string | null;
  departmentName: string | null;
  user: string | null;
  ding_user: string | null;
  dingUserId: string | null;
  create_time: string;
  update_time: string;
}

export interface AttendanceRuleItem {
  id: string;
  name: string;
  description: string;
  workday_start: string;
  workday_end: string;
  allow_late_minutes: number;
  allow_early_minutes: number;
  absence_minutes: number;
  overtime_start_minutes: number;
  weekend_as_workday: boolean;
  custom_workdays: number[];
  create_time: string;
  update_time: string;
}

export interface AttendanceDayDetailRecord {
  id: string;
  type: string;
  result: string;
  checkedAt: string;
  source: string;
}

export interface AttendanceDayDetail {
  status: string;
  lateMinutes?: number;
  earlyLeaveMinutes?: number;
  overtimeHours?: number;
  records: AttendanceDayDetailRecord[];
}

export interface AttendanceSummaryItem {
  id: string;
  employee: string;
  employeeName: string;
  employeeJobNumber: string;
  rule: string;
  ruleName: string;
  period_start: string;
  period_end: string;
  work_days: number;
  present_days: number;
  late_minutes: number;
  early_leave_minutes: number;
  absence_days: string;
  overtime_hours: string;
  detail: Record<string, AttendanceDayDetail>;
  status: number;
  statusLabel: string;
  create_time: string;
  update_time: string;
}

export interface PayrollRuleItem {
  id: string;
  name: string;
  description: string;
  overtime_rate: string | number;
  late_penalty_per_minute: string | number;
  absence_penalty_per_day: string | number;
  tax_rate: string | number;
  other_allowance: string | number;
  create_time: string;
  update_time: string;
}

export interface PayrollRecordItem {
  id: string;
  employee: string;
  employeeName: string;
  employeeJobNumber: string;
  rule: string;
  ruleName: string;
  attendance_summary: string | null;
  period_start: string;
  period_end: string;
  gross_salary: string;
  deductions: string;
  tax: string;
  net_salary: string;
  detail: Record<string, any>;
  remark: string;
  status: number;
  statusLabel: string;
  paid_at: string | null;
  create_time: string;
  update_time: string;
}

export interface ImportResult {
  created: number;
  updated: number;
}

export interface AttendanceCalculatePayload {
  ruleId: string;
  employeeIds: string[];
  start: string;
  end: string;
}

export interface AttendanceStatusPayload {
  ids: string[];
  status: number;
}

export interface PayrollCalculatePayload {
  ruleId: string;
  employeeIds: string[];
  periodStart: string;
  periodEnd: string;
}

export interface PayrollCalculateResult {
  records: PayrollRecordItem[];
  missing: Array<{ employeeId: string; name: string }>;
}

export const getHrDepartments = (params?: Record<string, any>) =>
  http.request<HrApiResponse<HrDepartment[]>>("get", "/api/hr/departments/", { params });

export const createHrDepartment = (data: Partial<HrDepartment>) =>
  http.request<HrApiResponse<HrDepartment>>("post", "/api/hr/departments/", { data });

export const updateHrDepartment = (id: string, data: Partial<HrDepartment>) =>
  http.request<HrApiResponse<HrDepartment>>("patch", `/api/hr/departments/${id}/`, { data });

export const deleteHrDepartment = (id: string) =>
  http.request<HrApiResponse<null>>("delete", `/api/hr/departments/${id}/`);

export const importHrDepartments = (data?: { configId?: string }) =>
  http.request<HrApiResponse<ImportResult>>("post", "/api/hr/departments/import/dingtalk/", { data });

export const getHrEmployees = (params?: Record<string, any>) =>
  http.request<HrApiResponse<HrEmployee[]>>("get", "/api/hr/employees/", { params });

export const createHrEmployee = (data: Partial<HrEmployee>) =>
  http.request<HrApiResponse<HrEmployee>>("post", "/api/hr/employees/", { data });

export const updateHrEmployee = (id: string, data: Partial<HrEmployee>) =>
  http.request<HrApiResponse<HrEmployee>>("patch", `/api/hr/employees/${id}/`, { data });

export const deleteHrEmployee = (id: string) =>
  http.request<HrApiResponse<null>>("delete", `/api/hr/employees/${id}/`);

export const importHrEmployees = (data?: { configId?: string }) =>
  http.request<HrApiResponse<ImportResult>>("post", "/api/hr/employees/import/dingtalk/", { data });

export const getAttendanceRules = (params?: Record<string, any>) =>
  http.request<HrApiResponse<AttendanceRuleItem[]>>("get", "/api/hr/attendance/rules/", { params });

export const createAttendanceRule = (data: Partial<AttendanceRuleItem>) =>
  http.request<HrApiResponse<AttendanceRuleItem>>("post", "/api/hr/attendance/rules/", { data });

export const updateAttendanceRule = (id: string, data: Partial<AttendanceRuleItem>) =>
  http.request<HrApiResponse<AttendanceRuleItem>>("patch", `/api/hr/attendance/rules/${id}/`, { data });

export const deleteAttendanceRule = (id: string) =>
  http.request<HrApiResponse<null>>("delete", `/api/hr/attendance/rules/${id}/`);

export const getAttendanceSummary = (params?: Record<string, any>) =>
  http.request<HrApiResponse<AttendanceSummaryItem[]>>("get", "/api/hr/attendance/summary/", { params });

export const calculateAttendance = (data: AttendanceCalculatePayload) =>
  http.request<HrApiResponse<AttendanceSummaryItem[]>>("post", "/api/hr/attendance/summary/calculate/", { data });

export const updateAttendanceStatus = (data: AttendanceStatusPayload) =>
  http.request<HrApiResponse<{ updated: number }>>("post", "/api/hr/attendance/summary/status/", { data });

export const getPayrollRules = (params?: Record<string, any>) =>
  http.request<HrApiResponse<PayrollRuleItem[]>>("get", "/api/hr/payroll/rules/", { params });

export const createPayrollRule = (data: Partial<PayrollRuleItem>) =>
  http.request<HrApiResponse<PayrollRuleItem>>("post", "/api/hr/payroll/rules/", { data });

export const updatePayrollRule = (id: string, data: Partial<PayrollRuleItem>) =>
  http.request<HrApiResponse<PayrollRuleItem>>("patch", `/api/hr/payroll/rules/${id}/`, { data });

export const deletePayrollRule = (id: string) =>
  http.request<HrApiResponse<null>>("delete", `/api/hr/payroll/rules/${id}/`);

export const getPayrollRecords = (params?: Record<string, any>) =>
  http.request<HrApiResponse<PayrollRecordItem[]>>("get", "/api/hr/payroll/records/", { params });

export const calculatePayroll = (data: PayrollCalculatePayload) =>
  http.request<HrApiResponse<PayrollCalculateResult>>("post", "/api/hr/payroll/records/calculate/", { data });
