import { defineStore } from "pinia";
import { message } from "@/utils/message";
import { store } from "../utils";
import {
  type HrDepartment,
  type HrEmployee,
  type AttendanceRuleItem,
  type AttendanceSummaryItem,
  type PayrollRuleItem,
  type PayrollRecordItem,
  type AttendanceCalculatePayload,
  type AttendanceStatusPayload,
  type PayrollCalculatePayload,
  type PayrollCalculateResult,
  getHrDepartments,
  createHrDepartment,
  updateHrDepartment,
  deleteHrDepartment,
  importHrDepartments,
  getHrEmployees,
  createHrEmployee,
  updateHrEmployee,
  deleteHrEmployee,
  importHrEmployees,
  getAttendanceRules,
  createAttendanceRule,
  updateAttendanceRule,
  deleteAttendanceRule,
  getAttendanceSummary,
  calculateAttendance,
  updateAttendanceStatus,
  getPayrollRules,
  createPayrollRule,
  updatePayrollRule,
  deletePayrollRule,
  getPayrollRecords,
  calculatePayroll
} from "@/api/hr";

interface HrState {
  departments: HrDepartment[];
  employees: HrEmployee[];
  attendanceRules: AttendanceRuleItem[];
  attendanceSummary: AttendanceSummaryItem[];
  payrollRules: PayrollRuleItem[];
  payrollRecords: PayrollRecordItem[];
  loading: boolean;
}

export const useHrStore = defineStore("pure-hr", {
  state: (): HrState => ({
    departments: [],
    employees: [],
    attendanceRules: [],
    attendanceSummary: [],
    payrollRules: [],
    payrollRecords: [],
    loading: false
  }),
  actions: {
    async fetchDepartments(params?: Record<string, any>) {
      this.loading = true;
      try {
        const res = await getHrDepartments(params);
        if (res.success) {
          this.departments = res.data;
        }
        return res;
      } finally {
        this.loading = false;
      }
    },
    async saveDepartment(payload: Partial<HrDepartment>) {
      const id = payload.id;
      const req = id ? updateHrDepartment(id, payload) : createHrDepartment(payload);
      const res = await req;
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchDepartments();
      }
      return res;
    },
    async removeDepartment(id: string) {
      const res = await deleteHrDepartment(id);
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchDepartments();
      }
      return res;
    },
    async importDepartments(configId?: string) {
      const res = await importHrDepartments({ configId });
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchDepartments();
      }
      return res;
    },
    async fetchEmployees(params?: Record<string, any>) {
      this.loading = true;
      try {
        const res = await getHrEmployees(params);
        if (res.success) {
          this.employees = res.data;
        }
        return res;
      } finally {
        this.loading = false;
      }
    },
    async saveEmployee(payload: Partial<HrEmployee>) {
      const id = payload.id;
      const req = id ? updateHrEmployee(id, payload) : createHrEmployee(payload);
      const res = await req;
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchEmployees();
      }
      return res;
    },
    async removeEmployee(id: string) {
      const res = await deleteHrEmployee(id);
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchEmployees();
      }
      return res;
    },
    async importEmployees(configId?: string) {
      const res = await importHrEmployees({ configId });
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchEmployees();
      }
      return res;
    },
    async fetchAttendanceRules(params?: Record<string, any>) {
      const res = await getAttendanceRules(params);
      if (res.success) {
        this.attendanceRules = res.data;
      }
      return res;
    },
    async saveAttendanceRule(payload: Partial<AttendanceRuleItem>) {
      const id = payload.id;
      const req = id ? updateAttendanceRule(id, payload) : createAttendanceRule(payload);
      const res = await req;
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchAttendanceRules();
      }
      return res;
    },
    async removeAttendanceRule(id: string) {
      const res = await deleteAttendanceRule(id);
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchAttendanceRules();
      }
      return res;
    },
    async fetchAttendanceSummary(params?: Record<string, any>) {
      const res = await getAttendanceSummary(params);
      if (res.success) {
        this.attendanceSummary = res.data;
      }
      return res;
    },
    async calculateAttendance(payload: AttendanceCalculatePayload) {
      const res = await calculateAttendance(payload);
      if (res.success) {
        message(res.msg, { type: "success" });
        this.attendanceSummary = res.data;
      }
      return res;
    },
    async updateAttendanceStatus(payload: AttendanceStatusPayload) {
      const res = await updateAttendanceStatus(payload);
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchAttendanceSummary();
      }
      return res;
    },
    async fetchPayrollRules(params?: Record<string, any>) {
      const res = await getPayrollRules(params);
      if (res.success) {
        this.payrollRules = res.data;
      }
      return res;
    },
    async savePayrollRule(payload: Partial<PayrollRuleItem>) {
      const id = payload.id;
      const req = id ? updatePayrollRule(id, payload) : createPayrollRule(payload);
      const res = await req;
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchPayrollRules();
      }
      return res;
    },
    async removePayrollRule(id: string) {
      const res = await deletePayrollRule(id);
      if (res.success) {
        message(res.msg, { type: "success" });
        await this.fetchPayrollRules();
      }
      return res;
    },
    async fetchPayrollRecords(params?: Record<string, any>) {
      const res = await getPayrollRecords(params);
      if (res.success) {
        this.payrollRecords = res.data;
      }
      return res;
    },
    async calculatePayroll(payload: PayrollCalculatePayload) {
      const res = await calculatePayroll(payload);
      if (res.success) {
        message(res.msg, { type: "success" });
        const data = res.data as PayrollCalculateResult;
        this.payrollRecords = data.records;
        if (data.missing.length) {
          message(`以下员工缺少考勤数据：${data.missing.map(item => item.name).join("、")}`, {
            type: "warning"
          });
        }
      }
      return res;
    }
  }
});

export function useHrStoreHook() {
  return useHrStore(store);
}
