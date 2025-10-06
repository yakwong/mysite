export default {
  path: "/hr",
  redirect: "/hr/departments",
  meta: {
    icon: "ri:team-line",
    title: "人力资源",
    rank: 4
  },
  children: [
    {
      path: "/hr/departments",
      name: "hr-departments",
      component: () => import("@/modules/hr/views/Departments.vue"),
      meta: {
        title: "部门管理",
        keepAlive: false
      }
    },
    {
      path: "/hr/employees",
      name: "hr-employees",
      component: () => import("@/modules/hr/views/Employees.vue"),
      meta: {
        title: "员工管理",
        keepAlive: false
      }
    },
    {
      path: "/hr/attendance/rules",
      name: "hr-attendance-rules",
      component: () => import("@/modules/hr/views/AttendanceRules.vue"),
      meta: {
        title: "考勤规则",
        keepAlive: false
      }
    },
    {
      path: "/hr/attendance/summary",
      name: "hr-attendance-summary",
      component: () => import("@/modules/hr/views/AttendanceSummary.vue"),
      meta: {
        title: "考勤统计",
        keepAlive: false
      }
    },
    {
      path: "/hr/payroll/rules",
      name: "hr-payroll-rules",
      component: () => import("@/modules/hr/views/PayrollRules.vue"),
      meta: {
        title: "薪资规则",
        keepAlive: false
      }
    },
    {
      path: "/hr/payroll/records",
      name: "hr-payroll-records",
      component: () => import("@/modules/hr/views/PayrollRecords.vue"),
      meta: {
        title: "薪资发放",
        keepAlive: false
      }
    }
  ]
} satisfies RouteConfigsTable;
