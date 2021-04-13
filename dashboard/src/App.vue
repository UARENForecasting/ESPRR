<!-- -->
<template>
  <div id="app">
    <header class="container">
      <!-- flex header with center aligned content -->
      <h1>ESPRR</h1>

      <div id="nav">
        <template v-if="$auth.isAuthenticated">
          <router-link to="/">Systems</router-link>
        </template>
      </div>

      <!-- Login/Logout at right of navbar-->
      <div id="nav-right">
        <template v-if="$auth.isAuthenticated">
          <button class="auth-button" @click="logout">Log out</button>
        </template>
        <template v-else>
          <button class="auth-button" @click="login">Log in</button>
        </template>
      </div>
    </header>
    <main>
      <template v-if="!$auth.loading">
        <!-- Only load render after we can check authentication -->
        <template v-if="$auth.isAuthenticated">
          <router-view />
        </template>
        <template v-else> Please log in to access ESPRR. </template>
      </template>

      <!-- Display loading indicator -->
      <template v-else> Loading... </template>
    </main>
  </div>
</template>
<script lang="ts">
import { Component, Vue } from "vue-property-decorator";

@Component
export default class App extends Vue {
  login(): void {
    this.$auth.loginWithRedirect();
  }
  logout(): void {
    this.$auth.logout({
      returnTo: window.location.origin,
    });
  }
}
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

header.container {
  background: #ddd;
  border-bottom: 5px solid #bbb;
  padding: 1em;
  align-items: center;
}
header h1 {
  color: white;
  text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000,
    1px 1px 0 #000;
}
#nav {
  flex: flex-grow;
  padding: 30px;
}

#nav a {
  font-weight: bold;
  color: #2c3e50;
}

#nav a.router-link-exact-active {
  color: #42b983;
}

#nav-right {
  margin-left: auto;
}

.auth-button {
  justify-self: right;
}
</style>
