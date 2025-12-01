<template>
  <div class="app">
    <NavBar />
    <main class="content">
      <div class="container">
        <router-view />
      </div>
    </main>
  </div>
  <el-backtop :right="24" :bottom="24" />
</template>

<script setup lang="ts">
import NavBar from './components/NavBar.vue'
</script>

<style scoped>
.app { min-height: 100vh; background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 40%); }
.content { padding: 24px; }
.container { max-width: 1080px; margin: 0 auto; }
</style>
<style>
html, body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Fira Sans", "Droid Sans", "Helvetica Neue", Arial, sans-serif; color: #1f2328; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
.title { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 18px; }
.subtitle { font-weight: 600; font-size: 16px; }
</style>
