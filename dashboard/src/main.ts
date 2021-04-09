import Vue from "vue";
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
    router.push(
      appState && appState.targetUrl
        ? appState.targetUrl
        : window.location.pathname
    );
  },
});

Vue.config.productionTip = false;

new Vue({
  router,
  render: (h) => h(App),
}).$mount("#app");
