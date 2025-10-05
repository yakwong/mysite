export default {
  path: "/dingtalk",
  meta: {
    icon: "ri:dingding-line",
    title: "钉钉中心",
    rank: 3
  },
  children: [
    {
      path: "/dingtalk/dashboard",
      name: "dingtalk-dashboard",
      component: () => import("@/modules/dingtalk/views/Dashboard.vue"),
      meta: {
        title: "总览",
        keepAlive: false
      }
    },
    {
      path: "/dingtalk/logs",
      name: "dingtalk-logs",
      component: () => import("@/modules/dingtalk/views/Logs.vue"),
      meta: {
        title: "同步日志",
        keepAlive: false
      }
    },
    {
      path: "/dingtalk/departments",
      name: "dingtalk-departments",
      component: () => import("@/modules/dingtalk/views/Departments.vue"),
      meta: {
        title: "部门数据",
        keepAlive: false
      }
    },
    {
      path: "/dingtalk/users",
      name: "dingtalk-users",
      component: () => import("@/modules/dingtalk/views/Users.vue"),
      meta: {
        title: "人员数据",
        keepAlive: false
      }
    },
    {
      path: "/dingtalk/attendance",
      name: "dingtalk-attendance",
      component: () => import("@/modules/dingtalk/views/Attendance.vue"),
      meta: {
        title: "考勤记录",
        keepAlive: false
      }
    },
    {
      path: "/dingtalk/settings",
      name: "dingtalk-settings",
      component: () => import("@/modules/dingtalk/views/Settings.vue"),
      meta: {
        title: "高级设置",
        keepAlive: false
      }
    }
  ]
} satisfies RouteConfigsTable;
