<template>
  <el-card>
    <div class="title"><el-icon><Picture /></el-icon><span>图片库</span></div>
    <div class="toolbar">
      <el-select v-model="status" placeholder="状态" style="width:140px" clearable @change="load">
        <el-option value="READY" label="READY" />
      </el-select>
      <el-select v-model="mime" placeholder="类型" style="width:160px" clearable @change="load">
        <el-option value="image/jpeg" label="JPEG" />
        <el-option value="image/png" label="PNG" />
        <el-option value="image/webp" label="WEBP" />
        <el-option value="image/gif" label="GIF" />
      </el-select>
      <el-select v-model="orderBy" placeholder="排序字段" style="width:160px" @change="load">
        <el-option value="created_at" label="创建时间" />
        <el-option value="id" label="ID" />
      </el-select>
      <el-select v-model="order" placeholder="顺序" style="width:120px" @change="load">
        <el-option value="desc" label="降序" />
        <el-option value="asc" label="升序" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
    </div>
    <el-row :gutter="16" style="margin-top:12px">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in items" :key="item.id">
        <el-card shadow="hover" class="card" @click="open(item.id)">
          <img class="thumb" :src="withJwtAbs(item.thumb_url)" alt="thumb" />
          <div class="meta">
            <div class="name">{{ item.original_filename }}</div>
            <div class="sub">ID: {{ item.id }} · {{ item.mime_type || 'unknown' }}</div>
          </div>
          <div class="actions">
            <el-button size="small" @click.stop="open(item.id)">详情</el-button>
            <el-button size="small" type="primary" @click.stop="download(item)">下载</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-pagination
      v-if="total>pageSize"
      style="margin-top:12px"
      background
      layout="prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="(p:number)=>{page=p; load()}"
    />
    <el-empty v-if="!items.length && inited" description="暂无图片，先去上传吧" style="margin-top: 16px;" />
  </el-card>
</template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const items = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const inited = ref(false)
const status = ref<string>('')
const mime = ref<string>('')
const orderBy = ref('created_at')
const order = ref('desc')

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/images', { params: { page: page.value, page_size: pageSize.value, status: status.value, mime: mime.value, order_by: orderBy.value, order: order.value } })
    items.value = data.data.items || []
    total.value = data.data.total || 0
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
    inited.value = true
  }
}

function open(id: number) {
  router.push(`/images/${id}`)
}

function toAbs(u: string) {
  try { return new URL(u, API_BASE).toString() } catch { return u }
}

function withJwtAbs(u: string) {
  const t = localStorage.getItem('token')
  if (!u) return u
  const abs = toAbs(u)
  const sep = abs.includes('?') ? '&' : '?'
  return t ? `${abs}${sep}jwt=${encodeURIComponent(t)}` : abs
}

function download(item: any) {
  window.open(withJwtAbs(item.download_url), '_blank')
}

onMounted(load)
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; }
.toolbar { display:flex; gap:8px; align-items:center; margin-top:8px; flex-wrap:wrap; }
.card { cursor:pointer; }
.thumb { width: 100%; height: 160px; object-fit: cover; border-radius: 4px; }
.meta { margin-top: 8px; }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sub { color: var(--el-text-color-secondary); font-size: 12px; }
.actions { display:flex; gap:8px; margin-top:8px; }
</style>
