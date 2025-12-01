<template>
  <el-card>
    <div class="title"><el-icon><Picture /></el-icon><span>Image Similarity Search</span></div>
    <el-input v-model.number="imageId" placeholder="Enter an existing Image ID (from upload result)" style="max-width: 360px" @keyup.enter.native="onSearch">
      <template #append>
        <el-button type="primary" :loading="loading" @click="onSearch">Search</el-button>
      </template>
    </el-input>
    <el-empty v-if="!rows.length && inited" description="No results. Confirm image_id exists or upload more images" style="margin-top: 16px;" />
    <el-row :gutter="12" v-if="rows.length" style="margin-top: 16px">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="row in rows" :key="row.image_id">
        <el-card shadow="hover" class="card" @click="open(row.image_id)">
          <img class="thumb" :src="withJwtAbs(row.thumb_url)" />
          <div class="meta">
            <div class="name">{{ row.original_filename }}</div>
            <el-progress :percentage="Math.round((row.similarity || 0) * 100)" :text-inside="true" :stroke-width="14" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
  <el-skeleton v-if="loading" :rows="4" animated style="margin-top: 12px" />
  </template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const imageId = ref<number | null>(null)
const rows = ref<any[]>([])
const loading = ref(false)
const inited = ref(false)

function toAbs(u: string) { try { return new URL(u, API_BASE).toString() } catch { return u } }
function withJwtAbs(u: string) {
  const t = localStorage.getItem('token')
  if (!u) return u
  const abs = toAbs(u)
  const sep = abs.includes('?') ? '&' : '?'
  return t ? `${abs}${sep}jwt=${encodeURIComponent(t)}` : abs
}

function open(id: number) { router.push(`/images/${id}`) }

async function onSearch() {
  if (!imageId.value) return ElMessage.warning('Please enter Image ID')
  loading.value = true
  try {
    const { data } = await api.get(`/search/image/${imageId.value}/similar`, { params: { k: 10 } })
    rows.value = data.data.results || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Search failed')
  } finally {
    loading.value = false
    inited.value = true
  }
}

onMounted(() => {
  const qid:any = route.query.id
  if (qid) {
    const num = Number(qid)
    if (!Number.isNaN(num)) {
      imageId.value = num
      onSearch()
    }
  }
})
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:8px; }
.card { cursor:pointer }
.thumb { width: 100%; height: 160px; object-fit: cover; border-radius:4px }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
