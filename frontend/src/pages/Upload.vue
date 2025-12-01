<template>
  <el-card>
    <div class="title"><el-icon><UploadFilled /></el-icon><span>上传图片</span></div>
    <el-upload drag :http-request="doUpload" :show-file-list="false" accept="image/*">
      <el-icon class="el-icon--upload"><Upload /></el-icon>
      <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
      <template #tip>
        <div class="el-upload__tip">仅支持图片类型，单次一张</div>
      </template>
    </el-upload>
    <el-divider />
    <el-result v-if="resp && resp.status==='ok'" icon="success" title="上传成功">
      <template #sub-title>
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="image_id">{{ resp.data.image_id }}</el-descriptions-item>
          <el-descriptions-item label="has_embedding">{{ String(resp.data.has_embedding) }}</el-descriptions-item>
          <el-descriptions-item label="has_ocr_text">{{ String(resp.data.has_ocr_text) }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:12px">
          <el-button type="primary" @click="goSimilar(resp.data.image_id)">查看相似</el-button>
          <el-button @click="copy(resp.data.image_id)">复制 image_id</el-button>
        </div>
      </template>
    </el-result>
    <el-alert v-else-if="resp && resp.status==='error'" type="error" :title="resp.message || '上传失败'" show-icon />
  </el-card>
</template>
<script setup lang="ts">
import api from '../api'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, UploadFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const resp = ref<any>(null)
const router = useRouter()

async function doUpload(options: any) {
  const form = new FormData()
  form.append('file', options.file)
  try {
    const { data } = await api.post('/files/upload', form, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000 })
    resp.value = data
    ElMessage.success('上传成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '上传失败')
  } finally {
    options.onSuccess?.(null)
  }
}

function goSimilar(id: number) {
  router.push({ path: '/similar', query: { id } })
}

async function copy(text: any) {
  try { await navigator.clipboard.writeText(String(text)); ElMessage.success('已复制'); } catch {}
}
</script>
