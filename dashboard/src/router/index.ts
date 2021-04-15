import VueRouter, { RouteConfig } from "vue-router";
import Systems from "../views/Systems.vue";
import SystemDefinition from "../views/SystemDefinition.vue";
import { authGuard } from "../auth/authGuard";

const routes: Array<RouteConfig> = [
  {
    path: "/",
    name: "Systems",
    component: Systems,
  },
  {
    path: "/system/new",
    name: "New System",
    component: SystemDefinition,
    beforeEnter: authGuard,
  },
  {
    path: "/system/:systemId",
    name: "Update System",
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
