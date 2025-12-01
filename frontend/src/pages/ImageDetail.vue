<template>
  <el-card>
    <div class="title"><el-icon><Picture /></el-icon><span>Image Details</span></div>
    <div class="layout">
      <div class="left">
        <el-skeleton v-if="loadingDetail" :rows="6" animated />
        <template v-else>
          <img class="big" :src="withJwtAbs(detail.thumb_url)" alt="thumb" />
          <el-descriptions :column="1" size="small" border style="margin-top:12px">
            <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
            <el-descriptions-item label="Filename">{{ detail.original_filename }}</el-descriptions-item>
            <el-descriptions-item label="Type">{{ detail.mime_type }}</el-descriptions-item>
            <el-descriptions-item label="Status">{{ detail.status }}</el-descriptions-item>
            <el-descriptions-item label="Embedding Dimension">{{ detail.embedding_dim }}</el-descriptions-item>
            <el-descriptions-item label="Has OCR">{{ String(detail.has_ocr_text) }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:12px">
            <el-button type="primary" @click="download">Download</el-button>
            <el-button type="danger" @click="remove" style="margin-left:8px">Delete</el-button>
          </div>
        </template>
      </div>
      <div class="right">
        <div class="subtitle">Similar Images</div>
        <el-skeleton v-if="loadingSim" :rows="6" animated />
        <div v-else>
          <el-empty v-if="!simRows.length" description="No similar images found" />
          <el-row :gutter="12">
            <el-col :xs="24" :sm="12" :md="12" :lg="12" v-for="row in simRows" :key="row.image_id">
              <el-card shadow="never" class="sim-card" @click="open(row.image_id)">
                <img class="thumb" :src="withJwtAbs(row.thumb_url)" />
                <div class="meta">
                  <div class="name">{{ row.original_filename }}</div>
                  <el-progress :percentage="Math.round((row.similarity || 0) * 100)" :text-inside="true" :stroke-width="14" />
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>
    </div>
  </el-card>
</template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const id = ref(Number(route.params.id))
const detail = ref<any>({})
const simRows = ref<any[]>([])
const loadingDetail = ref(true)
const loadingSim = ref(true)

function toAbs(u: string) { try { return new URL(u, API_BASE).toString() } catch { return u } }
function withJwtAbs(u: string) {
  const t = localStorage.getItem('token')
  if (!u) return u
  const abs = toAbs(u)
  const sep = abs.includes('?') ? '&' : '?'
  return t ? `${abs}${sep}jwt=${encodeURIComponent(t)}` : abs
}

async function loadDetail() {
  loadingDetail.value = true
  try {
    const { data } = await api.get(`/images/${id.value}`)
    detail.value = data.data || {}
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Failed to load image details')
  } finally {
    loadingDetail.value = false
  }
}

async function loadSimilar() {
  loadingSim.value = true
  try {
    const { data } = await api.get(`/search/image/${id.value}/similar`, { params: { k: 12 } })
    simRows.value = data.data.results || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Failed to load similar images')
  } finally {
    loadingSim.value = false
  }
}

function download() {
  window.open(withJwtAbs(detail.value.download_url), '_blank')
}

function open(targetId: number) {
  router.push(`/images/${targetId}`)
}

async function remove() {
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this image? This action cannot be undone.', 'Confirm Delete', { type: 'warning' })
    await api.delete(`/files/${id.value}`)
    ElMessage.success('Image deleted successfully')
    router.push('/gallery')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.message || 'Failed to delete image')
    }
  }
}

onMounted(() => { loadDetail(); loadSimilar() })
watch(() => route.params.id, (nid) => { id.value = Number(nid); loadDetail(); loadSimilar() })
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; }
.subtitle { font-weight:600; margin-bottom:8px; }
.layout { display:flex; gap:16px; }
.left { flex: 1; }
.right { width: 48%; }
.big { width: 100%; max-height: 420px; object-fit: contain; border-radius:4px; background:#fafafa; }
.sim-card { cursor:pointer; display:flex; gap:8px; align-items:center; }
.thumb { width: 96px; height: 96px; object-fit: cover; border-radius:4px; }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>