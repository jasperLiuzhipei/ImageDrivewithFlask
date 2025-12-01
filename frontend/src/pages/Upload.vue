<template>
  <el-card>
    <div class="title"><el-icon><UploadFilled /></el-icon><span>Image Upload</span></div>
    <el-upload
      drag
      multiple
      :file-list="batchFiles"
      :auto-upload="false"
      accept="image/*"
      @change="onBatchChange"
      @remove="onBatchRemove"
    >
      <el-icon class="el-icon--upload"><Upload /></el-icon>
      <div class="el-upload__text">Drag images here, or <em>click to select</em></div>
      <template #tip>
        <div class="el-upload__tip">Images only; select images then click Upload</div>
      </template>
    </el-upload>
    <div style="margin-top:12px">
      <el-button type="primary" :loading="uploadingBatch" :disabled="!batchFiles.length" @click="startBatch">Upload</el-button>
      <el-button :disabled="!batchFiles.length" @click="clearBatch" style="margin-left:8px">Clear</el-button>
    </div>
    <el-result v-if="batchResp && batchResp.status==='ok'" icon="success" title="Upload Successful">
      <template #sub-title>
        <div>Uploaded {{ batchResp.data.count }} images</div>
      </template>
    </el-result>
    <el-alert v-else-if="batchResp && batchResp.status==='error'" type="error" :title="batchResp.message || 'Upload Failed'" show-icon />
  </el-card>
</template>
<script setup lang="ts">
import api from '../api'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, UploadFilled } from '@element-plus/icons-vue'

const resp = ref<any>(null)
const batchFiles = ref<any[]>([])
const uploadingBatch = ref(false)
const batchResp = ref<any>(null)

function onBatchChange(_file: any, files: any[]) {
  batchFiles.value = files
}

function onBatchRemove(_file: any, files: any[]) {
  batchFiles.value = files
}

function clearBatch() {
  batchFiles.value = []
  batchResp.value = null
}

async function startBatch() {
  if (!batchFiles.value.length) return
  uploadingBatch.value = true
  const form = new FormData()
  for (const f of batchFiles.value) {
    const raw = f.raw || f
    form.append('files', raw)
  }
  try {
    const { data } = await api.post('/files/upload/batch', form, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
    batchResp.value = data
    ElMessage.success('Upload successful')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Upload failed')
  } finally {
    uploadingBatch.value = false
  }
}
</script>
