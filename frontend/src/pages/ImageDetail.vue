<template>
  <el-card>
    <div class="title"><el-icon><Picture /></el-icon><span>图片详情</span></div>
    <div class="layout">
      <div class="left">
        <el-skeleton v-if="loadingDetail" :rows="6" animated />
        <template v-else>
          <img class="big" :src="withJwtAbs(detail.thumb_url)" alt="thumb" />
          <el-descriptions :column="1" size="small" border style="margin-top:12px">
            <el-descriptions-item label="ID">{{ detail.id }}</el-descriptions-item>
            <el-descriptions-item label="文件名">{{ detail.original_filename }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ detail.mime_type }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ detail.status }}</el-descriptions-item>
            <el-descriptions-item label="嵌入维度">{{ detail.embedding_dim }}</el-descriptions-item>
            <el-descriptions-item label="有 OCR">{{ String(detail.has_ocr_text) }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:12px">
            <el-button type="primary" @click="download">下载</el-button>
          </div>
        </template>
      </div>
      <div class="right">
        <div class="subtitle">相似图片</div>
        <el-skeleton v-if="loadingSim" :rows="6" animated />
        <div v-else>
          <el-empty v-if="!simRows.length" description="暂无相似项" />
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
import { ElMessage } from 'element-plus'
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
    ElMessage.error(e?.response?.data?.message || '加载失败')
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
    ElMessage.error(e?.response?.data?.message || '相似检索失败')
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
