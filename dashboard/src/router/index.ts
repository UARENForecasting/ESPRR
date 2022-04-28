import VueRouter, { RouteConfig } from "vue-router";
import Systems from "../views/Systems.vue";
import Groups from "../views/Groups.vue";
import SystemDefinition from "../views/SystemDefinition.vue";
import GroupDefinition from "../views/GroupDefinition.vue";
import SystemDetails from "../views/System.vue";
import GroupDetails from "../views/Group.vue";

import { authGuard } from "../auth/authGuard";

const routes: Array<RouteConfig> = [
  {
    path: "/",
    name: "Systems",
    component: Systems,
  },
  {
    path: "/groups",
    name: "Groups",
    component: Groups,
  },
  {
    path: "/system/new",
    name: "New System",
    component: SystemDefinition,
    beforeEnter: authGuard,
  },
  {
    path: "/system_group/new",
    name: "New Group",
    component: GroupDefinition,
    beforeEnter: authGuard,
  },
  {
    path: "/system_group/:groupId/edit",
    name: "Update Group",
    component: GroupDefinition,
    props: true,
    beforeEnter: authGuard,
  },
  {
    path: "/system/:systemId/:dataset",
    name: "System Details",
    component: SystemDetails,
    props: true,
    beforeEnter: authGuard,
  },
  {
    path: "/system_group/:groupId",
    name: "Group Details",
    component: GroupDetails,
    props: true,
    beforeEnter: authGuard,
  },
  {
    path: "/system_group/:groupId/:dataset",
    name: "Group Dataset Details",
    component: GroupDetails,
    props: true,
    beforeEnter: authGuard,
  },
  {
    path: "/system/:systemId/edit",
    name: "Update System",
    component: SystemDefinition,
    props: true,
    beforeEnter: authGuard,
  },
  {
    path: "/system/:systemId/edit/:dataset",
    name: "Update System dataset return",
    component: SystemDefinition,
    props: true,
    beforeEnter: authGuard,
  },
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes,
});

export default router;
