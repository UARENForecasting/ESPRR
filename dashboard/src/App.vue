<template>
  <div id="app">
    <div id="nav">
      <span v-if="!$auth.loading && $auth.isAuthenticated">
        <router-link to="/">Systems</router-link> |
      </span>
    </div>
    <span v-if="$auth.isAuthenticated">
      <button @click="logout">Log out</button>
    </span>
    <span v-else>
      <button @click="login">Log in</button>
    </span>
    <router-view />
  </div>
</template>
<script lang="ts">
import { Component, Vue } from "vue-property-decorator";

@Component
export default class App extends Vue {
  login() {
    this.$auth.loginWithRedirect();
  }
  logout() {
    this.$auth.logout({
      returnTo: window.location.origin,
    });
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

#nav {
  padding: 30px;
}

#nav a {
  font-weight: bold;
  color: #2c3e50;
}

#nav a.router-link-exact-active {
  color: #42b983;
}
</style>
