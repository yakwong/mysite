<script setup lang="ts">
import { deviceDetection } from "@pureadmin/utils";
import { getSecurityLogs, type SecurityLogItem } from "@/api/user";
import { onMounted, reactive, ref } from "vue";
import type { PaginationProps, TableColumnList } from "@pureadmin/table";

const loading = ref(true);
const dataList = ref<SecurityLogItem[]>([]);
const pagination = reactive<PaginationProps>({
  total: 0,
  pageSize: 10,
  currentPage: 1,
  background: true,
  layout: "prev, pager, next",
  pageSizes: [10, 20, 50]
});

const columns: TableColumnList = [
  {
    label: "详情",
    prop: "summary",
    minWidth: 140
  },
  {
    label: "IP 地址",
    prop: "ip",
    minWidth: 120
  },
  {
    label: "地点",
    prop: "address",
    minWidth: 140
  },
  {
    label: "操作系统",
    prop: "system",
    minWidth: 120
  },
  {
    label: "浏览器类型",
    prop: "browser",
    minWidth: 120
  },
  {
    label: "时间",
    prop: "operating_time",
    minWidth: 180
  },
  {
    label: "状态",
    prop: "status",
    minWidth: 100,
    formatter: ({ row }) => (row.status ? "成功" : "失败")
  }
];

async function fetchLogs(page = pagination.currentPage, size = pagination.pageSize) {
  loading.value = true;
  try {
    const { data } = await getSecurityLogs({ page, limit: size });
    dataList.value = data.list;
    pagination.total = data.total;
    pagination.pageSize = data.pageSize;
    pagination.currentPage = data.currentPage;
  } finally {
    loading.value = false;
  }
}

function handleCurrentChange(page: number) {
  fetchLogs(page, pagination.pageSize);
}

function handleSizeChange(size: number) {
  pagination.pageSize = size;
  fetchLogs(1, size);
}

onMounted(() => {
  fetchLogs();
});
</script>

<template>
  <div :class="['min-w-[180px]', deviceDetection() ? 'max-w-[100%]' : 'max-w-[70%]']">
    <h3 class="my-8!">安全日志</h3>
    <pure-table row-key="id" table-layout="auto" :loading="loading" :data="dataList" :columns="columns" :pagination="pagination" @page-current-change="handleCurrentChange" @page-size-change="handleSizeChange" />
  </div>
</template>
