// 这里存放本地图标，在 src/layout/index.vue 文件中加载，避免在首启动加载
import { getSvgInfo } from "@pureadmin/utils";
import { addIcon } from "@iconify/vue/dist/offline";

// https://icon-sets.iconify.design/ep/?keyword=ep
import EpHomeFilled from "~icons/ep/home-filled?raw";
import EpHouse from "~icons/ep/house?raw";
import EpOfficeBuilding from "~icons/ep/office-building?raw";
import EpMenu from "~icons/ep/menu?raw";
import EpSetting from "~icons/ep/setting?raw";
import EpUser from "~icons/ep/user?raw";
import EpPaperclip from "~icons/ep/paperclip?raw";
import EpCalendar from "~icons/ep/calendar?raw";
import EpTrendCharts from "~icons/ep/trend-charts?raw";
import EpCoin from "~icons/ep/coin?raw";
import EpDocument from "~icons/ep/document?raw";
import EpMonitor from "~icons/ep/monitor?raw";

// https://icon-sets.iconify.design/ri/?keyword=ri
import RiSearchLine from "~icons/ri/search-line?raw";
import RiInformationLine from "~icons/ri/information-line?raw";
import RiTeamLine from "~icons/ri/team-line?raw";
import RiGroupLine from "~icons/ri/group-line?raw";
import RiLoginCircleLine from "~icons/ri/login-circle-line?raw";
import RiNodeTree from "~icons/ri/node-tree?raw";
import RiTestTubeLine from "~icons/ri/test-tube-line?raw";
import RiMacLine from "~icons/ri/mac-line?raw";
import RiDingdingLine from "~icons/ri/dingding-line?raw";

const icons = [
  // Element Plus Icon: https://github.com/element-plus/element-plus-icons
  ["ep:home-filled", EpHomeFilled],
  ["ep:house", EpHouse],
  ["ep:office-building", EpOfficeBuilding],
  ["ep:menu", EpMenu],
  ["ep:setting", EpSetting],
  ["ep:user", EpUser],
  ["ep:paperclip", EpPaperclip],
  ["ep:calendar", EpCalendar],
  ["ep:trend-charts", EpTrendCharts],
  ["ep:coin", EpCoin],
  ["ep:document", EpDocument],
  ["ep:monitor", EpMonitor],
  // Remix Icon: https://github.com/Remix-Design/RemixIcon
  ["ri:search-line", RiSearchLine],
  ["ri:information-line", RiInformationLine],
  ["ri:team-line", RiTeamLine],
  ["ri:group-line", RiGroupLine],
  ["ri:login-circle-line", RiLoginCircleLine],
  ["ri:node-tree", RiNodeTree],
  ["ri:test-tube-line", RiTestTubeLine],
  ["ri:mac-line", RiMacLine],
  ["ri:dingding-line", RiDingdingLine]
];

// 本地菜单图标，后端在路由的 icon 中返回对应的图标字符串并且前端在此处使用 addIcon 添加即可渲染菜单图标
icons.forEach(([name, icon]) => {
  addIcon(name as string, getSvgInfo(icon as string));
});
