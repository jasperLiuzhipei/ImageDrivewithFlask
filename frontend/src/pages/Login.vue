<template>
  <el-card class="card">
    <div class="title"><el-icon><User /></el-icon><span>登录</span></div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" @keyup.enter="onLogin">
      <el-form-item label="用户名" prop="username"><el-input v-model="form.username" clearable /></el-form-item>
      <el-form-item label="密码" prop="password"><el-input v-model="form.password" show-password /></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onLogin" :loading="loading">登录</el-button>
        <el-button link @click="$router.push('/register')">去注册</el-button>
      </el-form-item>
    </el-form>
  </el-card>
  <el-result v-if="errorMsg" icon="warning" :title="'登录失败'" :sub-title="errorMsg" />
</template>
<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../store_auth'

const router = useRouter()
const route = useRoute()
const auth = useAuth()
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMsg = ref('')

async function onLogin() {
  errorMsg.value = ''
  await formRef.value?.validate()
  loading.value = true
  try {
    await auth.login(form.username.trim(), form.password)
    router.push('/upload')
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.message || '请检查用户名或密码'
    ElMessage.error(errorMsg.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const qname = route.query.username
  if (typeof qname === 'string') {
    form.username = qname
  }
})
</script>
<style scoped>
.card { max-width: 420px; margin: 56px auto; }
.title { display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:8px; }
</style>
