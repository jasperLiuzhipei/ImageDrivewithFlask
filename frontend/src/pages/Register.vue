<template>
  <el-card class="card">
    <div class="title"><el-icon><UserFilled /></el-icon><span>Sign Up</span></div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" @keyup.enter="onRegister">
      <el-form-item label="Username" prop="username"><el-input v-model="form.username" clearable /></el-form-item>
      <el-form-item label="Password" prop="password"><el-input v-model="form.password" show-password /></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onRegister" :loading="loading">Sign Up</el-button>
        <el-button link @click="$router.push('/login')">Sign In</el-button>
      </el-form-item>
    </el-form>
  </el-card>
  <el-result v-if="success" icon="success" title="Sign-up Successful" sub-title="You can sign in now" />
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../store_auth'

const router = useRouter()
const auth = useAuth()
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: 'Please enter username', trigger: 'blur' }],
  password: [{ required: true, message: 'Please enter password', trigger: 'blur' }]
}
const formRef = ref<FormInstance>()
const loading = ref(false)
const success = ref(false)

async function onRegister() {
  success.value = false
  await formRef.value?.validate()
  loading.value = true
  try {
    await auth.register(form.username.trim(), form.password)
    success.value = true
    ElMessage.success('Sign-up successful, please sign in')
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Registration failed')
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.card { max-width: 420px; margin: 56px auto; }
.title { display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:8px; }
</style>
