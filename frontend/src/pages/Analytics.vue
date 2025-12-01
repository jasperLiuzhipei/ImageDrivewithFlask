<template>
  <el-card>
    <div class="title"><el-icon><DataAnalysis /></el-icon><span>数据概览</span></div>
    <div class="cards">
      <el-statistic title="图片总量" :value="summary.total" />
      <el-statistic title="嵌入覆盖率" :value="Math.round((summary.embedding_coverage?.ratio||0)*100)+'%'" />
      <el-statistic title="OCR 覆盖率" :value="Math.round((summary.ocr_coverage?.ratio||0)*100)+'%'" />
      <el-statistic title="重复计数" :value="summary.duplicate_count" />
    </div>
    <el-row :gutter="16" style="margin-top:12px">
      <el-col :md="12" :xs="24">
        <el-card shadow="never" header="MIME 分布">
          <el-table :data="mimeRows" size="small"><el-table-column prop="k" label="MIME"/><el-table-column prop="v" label="数量"/></el-table></el-card>
      </el-col>
      <el-col :md="12" :xs="24">
        <el-card shadow="never" header="日上传">
          <el-table :data="dayRows" size="small"><el-table-column prop="k" label="日期"/><el-table-column prop="v" label="数量"/></el-table></el-card>
      </el-col>
    </el-row>
    <el-card shadow="never" header="存储与索引" style="margin-top:12px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="uploads 大小(B)">{{ storage.uploads_size_bytes }}</el-descriptions-item>
        <el-descriptions-item label="index 大小(B)">{{ storage.index_size_bytes }}</el-descriptions-item>
        <el-descriptions-item label="index 目录">{{ storage.index_dir }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-card shadow="never" header="性能快照" style="margin-top:12px">
      <el-table :data="perfRows" size="small">
        <el-table-column prop="action" label="action" />
        <el-table-column prop="count" label="count" />
        <el-table-column prop="avg_ms" label="avg_ms" />
        <el-table-column prop="p90_ms" label="p90_ms" />
        <el-table-column prop="p99_ms" label="p99_ms" />
      </el-table>
    </el-card>
    <div style="margin-top:12px; display:flex; gap:8px">
      <el-button @click="downloadJson">下载 JSON</el-button>
      <el-button type="primary" @click="downloadCsv">下载 CSV</el-button>
    </div>
  </el-card>
</template>
<script setup lang="ts">
import api from '../api'
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

function downloadJson() { window.open('/api/v1/analytics/export.json', '_blank') }
function downloadCsv() { window.open('/api/v1/analytics/export.csv', '_blank') }

onMounted(load)
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; }
.cards { display:flex; gap:16px; flex-wrap:wrap; }
</style>
