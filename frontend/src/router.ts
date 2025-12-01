import { createRouter, createWebHistory } from 'vue-router'
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Upload from './pages/Upload.vue'
import SearchText from './pages/SearchText.vue'
import SearchOCR from './pages/SearchOCR.vue'
import Similar from './pages/Similar.vue'
import Health from './pages/Health.vue'
import Gallery from './pages/Gallery.vue'
import ImageDetail from './pages/ImageDetail.vue'
import Analytics from './pages/Analytics.vue'
import Logs from './pages/Logs.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/upload' },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/upload', component: Upload },
    { path: '/search/text', component: SearchText },
    { path: '/search/ocr', component: SearchOCR },
    { path: '/similar', component: Similar },
    { path: '/health', component: Health },
    { path: '/gallery', component: Gallery },
    { path: '/images/:id', component: ImageDetail },
    { path: '/analytics', component: Analytics },
    { path: '/logs', component: Logs }
  ]
})

// 简单的登录校验：无令牌则禁止访问非公开页面
const PUBLIC_PATHS = new Set(['/login', '/register', '/health'])
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token') || ''
  if (!token && !PUBLIC_PATHS.has(to.path)) {
    next('/login')
  } else {
    next()
  }
})
