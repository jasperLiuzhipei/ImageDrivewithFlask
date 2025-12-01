import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import { router } from './router'
import { enforceSessionOnLoad, bindActivityListeners } from './session'
import { useAuth } from './store_auth'

const app = createApp(App)
app.use(createPinia())
app.use(ElementPlus)
app.use(router)
app.mount('#app')

// 会话策略：应用加载时检查，绑定活跃事件
enforceSessionOnLoad()
bindActivityListeners()

// 刷新后根据本地 token 还原用户信息，避免导航条回退到未登录状态
try { const auth = useAuth(); if (auth.token && !auth.user) auth.me() } catch {}
