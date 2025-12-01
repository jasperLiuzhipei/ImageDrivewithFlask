<template>
  <el-card>
    <div class="title"><el-icon><List /></el-icon><span>Logs</span></div>
    <div class="toolbar">
      <el-select v-model="action" placeholder="Action" clearable style="width:180px" @change="load">
        <el-option v-for="a in actions" :key="a" :value="a" :label="a" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="load">Refresh</el-button>
      <el-button @click="exportCsv">Export CSV</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" style="margin-top:12px">
      <el-table-column prop="id" label="#" width="80" />
      <el-table-column prop="action" label="action" width="160" />
      <el-table-column prop="entity_type" label="entity_type" width="140" />
      <el-table-column prop="entity_id" label="entity_id" width="120" />
      <el-table-column prop="created_at" label="created_at" width="220" />
      <el-table-column label="extra">
        <template #default="{ row }">
          <pre class="extra">{{ JSON.stringify(row.extra || {}, null, 0) }}</pre>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total>pageSize" style="margin-top:12px" background layout="prev, pager, next" :total="total" :page-size="pageSize" :current-page="page" @current-change="(p:number)=>{page=p; load()}" />
  </el-card>
</template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref, onMounted } from 'vue'
import { List } from '@element-plus/icons-vue'

const action = ref<string>('')
const actions = ['upload','download','thumb','search_text','search_vector','similar_images']
const rows = ref<any[]>([])
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/logs', { params: { page: page.value, page_size: pageSize.value, action: action.value } })
    rows.value = data.data.items || []
    total.value = data.data.total || 0
  } finally { loading.value = false }
}

async function exportCsv() {
  const params:any = {}
  if (action.value) params.action = action.value
  const resp = await api.get('/logs/export', { params, responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'logs.csv'
  document.body.appendChild(a)
  a.click()
  URL.revokeObjectURL(url)
  a.remove()
}

onMounted(load)
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:8px; }
.toolbar { display:flex; gap:8px; align-items:center; margin-top:8px; flex-wrap:wrap; }
.toolbar :deep(.el-select) { width: 180px; }
.toolbar :deep(.el-button) { min-width: 120px; }
.extra { margin:0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
