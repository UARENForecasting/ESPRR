<!-- -->
<template>
  <div id="app">
    <header class="container">
      <!-- flex header with center aligned content -->
      <div>
        <h1>ESPRR</h1>
        <h5>
          Expected Solar Performance<br />
          and Ramp Rate Tool
        </h5>
      </div>

      <div id="nav">
        <template v-if="$auth.isAuthenticated">
          <router-link to="/">Systems</router-link>
        </template>
        <a href="/api/docs">API Documentation</a>
        <a href="https://github.com/uarenforecasting/esprr">Code</a>
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
        <template v-else>
          <div class="intro">
            <p>
              The Expected Solar Performance and Ramp Rate Tool (ESPRR) is an
              open source, interactive web application to model expected power
              and ramp rates for solar PV plants in the Southwest. It accounts
              for plant location, size, orientation, and geographic extent. The
              tool consists of this web frontend backed by a REST API (<a
                href="/api/docs"
                >API documentation</a
              >).
            </p>
            <p>Please log in to access ESPRR.</p>
          </div>
        </template>
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
  padding: 0.2em 1em;
  align-items: center;
}
header h1 {
  display: inline;
  color: white;
  text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000,
    1px 1px 0 #000;
}
header h5 {
  margin-left: 1em;
  display: inline-block;
  color: #888;
}
#nav {
  flex: flex-grow;
  padding: 30px;
}

#nav a {
  font-weight: bold;
  color: #2c3e50;
  padding: 0 0.5em;
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

.intro {
  padding: 2em;
  max-width: 1024px;
}
</style>
