<template>
  <el-card>
    <div class="title"><el-icon><Search /></el-icon><span>Text Search</span></div>
    <el-input v-model="q" placeholder="Enter query, e.g., a cat on a chair" style="max-width: 520px" @keyup.enter.native="onSearch">
      <template #append>
        <el-button type="primary" :loading="loading" @click="onSearch">Search</el-button>
      </template>
    </el-input>
    <el-empty v-if="!rows.length && inited" description="No results. Try other keywords" style="margin-top: 16px;" />
    <el-row :gutter="12" v-if="rows.length" style="margin-top: 16px">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="row in rows" :key="row.image_id">
        <el-card shadow="hover" class="card">
          <img class="thumb" :src="withJwtAbs(row.thumb_url)" />
          <div class="meta">
            <div class="name">{{ row.original_filename }}</div>
            <el-progress :percentage="Math.round((row.similarity || 0) * 100)" :text-inside="true" :stroke-width="14" />
            <div style="margin-top:6px"><el-button size="small" @click="goSimilar(row.image_id)">View Similar</el-button></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
  <el-skeleton v-if="loading" :rows="4" animated style="margin-top: 12px" />
</template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const q = ref('a cat sitting on a chair')
const rows = ref<any[]>([])
const loading = ref(false)
const inited = ref(false)
const router = useRouter()

function toAbs(u: string) { try { return new URL(u, API_BASE).toString() } catch { return u } }
function withJwtAbs(u: string) {
  const t = localStorage.getItem('token')
  if (!u) return u
  const abs = toAbs(u)
  const sep = abs.includes('?') ? '&' : '?'
  return t ? `${abs}${sep}jwt=${encodeURIComponent(t)}` : abs
}

async function onSearch() {
  loading.value = true
  try {
    const { data } = await api.post('/search/text', { query: q.value, k: 10 })
    rows.value = data.data.results || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Search failed')
  } finally {
    loading.value = false
    inited.value = true
  }
}

function goSimilar(id: number) {
  router.push({ path: '/similar', query: { id } })
}
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:8px; }
.card { cursor:default }
.thumb { width: 100%; height: 160px; object-fit: cover; border-radius:4px }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
