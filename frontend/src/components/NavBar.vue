<template>
  <el-header class="nav">
    <div class="brand" @click="$router.push('/')">
      <el-icon><Picture /></el-icon>
      <span>Web Image Drive</span>
    </div>
    <el-menu mode="horizontal" :ellipsis="false" class="menu" router>
      <el-menu-item index="/upload">上传</el-menu-item>
      <el-menu-item index="/gallery">图片库</el-menu-item>
      <el-menu-item index="/search/text">文本检索</el-menu-item>
      <el-menu-item index="/search/ocr">OCR 检索</el-menu-item>
      <el-menu-item index="/similar">以图搜图</el-menu-item>
      <el-menu-item index="/analytics">分析</el-menu-item>
      <el-menu-item index="/logs">日志</el-menu-item>
      <el-menu-item index="/health">健康</el-menu-item>
    </el-menu>
    <div class="right">
      <template v-if="auth.user">
        <el-dropdown>
          <span class="el-dropdown-link user">
            <el-avatar size="small">{{ initials }}</el-avatar>
            <span class="username">{{ auth.user.username }}</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="openChange">修改密码</el-dropdown-item>
              <el-dropdown-item @click="onLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dialog v-model="showChange" title="修改密码" width="420px">
          <el-form :model="form" label-width="96px">
            <el-form-item label="原密码"><el-input v-model="form.old" show-password /></el-form-item>
            <el-form-item label="新密码"><el-input v-model="form.n1" show-password /></el-form-item>
            <el-form-item label="确认新密码"><el-input v-model="form.n2" show-password /></el-form-item>
          </el-form>
          <template #footer>
            <div style="display:flex; justify-content:flex-end; gap:8px;">
              <el-button @click="onCancel">取消</el-button>
              <el-button type="primary" :loading="loading" @click="onConfirm">确认</el-button>
            </div>
          </template>
        </el-dialog>
      </template>
      <template v-else>
        <el-button link @click="$router.push('/login')">登录</el-button>
        <el-button type="primary" @click="$router.push('/register')">注册</el-button>
      </template>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAuth } from '../store_auth'
import { ArrowDown, Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const auth = useAuth()
const initials = computed(() => (auth.user?.username?.[0] || 'U').toUpperCase())
const router = useRouter()
const showChange = ref(false)
const loading = ref(false)
const form = reactive({ old: '', n1: '', n2: '' })

function onLogout() {
  auth.logout()
}

function openChange() {
  showChange.value = true
}

function onCancel() {
  showChange.value = false
  form.old = ''
  form.n1 = ''
  form.n2 = ''
}

async function onConfirm() {
  if (!form.old || !form.n1 || !form.n2) return ElMessage.warning('请输入完整信息')
  if (form.n1 !== form.n2) return ElMessage.warning('两次新密码不一致')
  loading.value = true
  const username = auth.user?.username || ''
  try {
    await auth.changePassword(form.old, form.n1)
    ElMessage.success('修改成功，请重新登录')
    onCancel()
    auth.logout()
    router.push({ path: '/login', query: { username } })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '修改失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.nav {
  display: flex;
  align-items: center;
  gap: 20px;
  border-bottom: 1px solid var(--el-border-color);
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  cursor: pointer;
}
.menu {
  flex: 1;
}
.right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user { display: inline-flex; align-items: center; gap: 6px; }
.username { font-size: 14px; color: var(--el-text-color-regular); }
</style>
