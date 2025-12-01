<template>
  <el-card>
    <div class="title"><el-icon><DataAnalysis /></el-icon><span>Data Overview</span></div>
    <div class="cards">
      <el-statistic title="Total Images" :value="summary.total" />
      <el-statistic title="Embedding Coverage" :value="Math.round((summary.embedding_coverage?.ratio||0)*100)+'%'" />
      <el-statistic title="OCR Coverage" :value="Math.round((summary.ocr_coverage?.ratio||0)*100)+'%'" />
      <el-statistic title="Duplicate Count" :value="summary.duplicate_count" />
    </div>
    <el-row :gutter="16" style="margin-top:12px">
      <el-col :md="12" :xs="24">
        <el-card shadow="never" header="MIME Distribution">
          <el-table :data="mimeRows" size="small"><el-table-column prop="k" label="MIME Type"/><el-table-column prop="v" label="Count"/></el-table></el-card>
      </el-col>
      <el-col :md="12" :xs="24">
        <el-card shadow="never" header="Daily Uploads">
          <el-table :data="dayRows" size="small"><el-table-column prop="k" label="Date"/><el-table-column prop="v" label="Uploads"/></el-table></el-card>
      </el-col>
    </el-row>
    <el-card shadow="never" header="Storage & Index" style="margin-top:12px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="Uploads Size (Bytes)">{{ storage.uploads_size_bytes }}</el-descriptions-item>
        <el-descriptions-item label="Index Size (Bytes)">{{ storage.index_size_bytes }}</el-descriptions-item>
        <el-descriptions-item label="Index Directory">{{ storage.index_dir }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-card shadow="never" header="Performance Snapshot" style="margin-top:12px">
      <el-table :data="perfRows" size="small">
        <el-table-column prop="action" label="Action" />
        <el-table-column prop="count" label="Count" />
        <el-table-column prop="avg_ms" label="Avg (ms)" />
        <el-table-column prop="p90_ms" label="P90 (ms)" />
        <el-table-column prop="p99_ms" label="P99 (ms)" />
      </el-table>
    </el-card>
    <div style="margin-top:12px; display:flex; gap:8px">
      <el-button @click="downloadJson">Download JSON</el-button>
      <el-button type="primary" @click="downloadCsv">Download CSV</el-button>
    </div>
  </el-card>
</template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref, onMounted } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'

const summary = ref<any>({})
const storage = ref<any>({})
const perfRows = ref<any[]>([])
const mimeRows = ref<any[]>([])
const dayRows = ref<any[]>([])

async function load() {
  const s = await api.get('/analytics/summary')
  summary.value = s.data.data || {}
  mimeRows.value = Object.entries(summary.value.mime_distribution || {}).map(([k, v]) => ({ k, v }))
  dayRows.value = Object.entries(summary.value.daily_uploads || {}).map(([k, v]) => ({ k, v }))
  const st = await api.get('/analytics/storage')
  storage.value = st.data.data || {}
  const pf = await api.get('/analytics/perf')
  const stats = (pf.data.data?.stats || {}) as Record<string, any>
  perfRows.value = Object.keys(stats).map(k => ({ action: k, ...stats[k] }))
}

function toAbs(u: string) { try { return new URL(u, API_BASE).toString() } catch { return u } }
function withJwtAbs(u: string) {
  const t = localStorage.getItem('token')
  const abs = toAbs(u)
  const sep = abs.includes('?') ? '&' : '?'
  return t ? `${abs}${sep}jwt=${encodeURIComponent(t)}` : abs
}

async function downloadJson() {
  const resp = await api.get('/analytics/export.json', { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'analytics.json'
  document.body.appendChild(a)
  a.click()
  URL.revokeObjectURL(url)
  a.remove()
}
async function downloadCsv() {
  const resp = await api.get('/analytics/export.csv', { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'analytics.csv'
  document.body.appendChild(a)
  a.click()
  URL.revokeObjectURL(url)
  a.remove()
}

onMounted(load)
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; }
.cards { display:flex; gap:16px; flex-wrap:wrap; }
</style>