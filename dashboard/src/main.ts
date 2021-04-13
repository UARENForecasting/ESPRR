import Vue from "vue";
import VueRouter from "vue-router";
import App from "./App.vue";
import router from "./router";

import "./assets/css/styles.css";

// Auth0 config
import { domain, clientId, audience } from "../auth_config.json";
import { Auth0Plugin } from "./auth/auth";

Vue.use(Auth0Plugin, {
  domain,
  clientId,
  audience,
  onredirectCallback: (appState: { targetUrl: string }) => {
    /* istanbul ignore next */
    router.push(
      appState && appState.targetUrl
        ? appState.targetUrl
        : window.location.pathname
    );
  },
});

Vue.use(VueRouter);

Vue.config.productionTip = false;

new Vue({
  router,
  render: (h) => h(App),
}).$mount("#app");
