<template>
  <el-card>
    <div class="title"><el-icon><Picture /></el-icon><span>Gallery</span></div>
    <div class="toolbar">
      <el-select v-model="status" placeholder="Status" style="width:180px" clearable @change="load">
        <el-option value="READY" label="READY" />
        <el-option value="favorite" label="FAVORITE" />
      </el-select>
      <el-select v-model="mime" placeholder="Type" style="width:180px" clearable @change="load">
        <el-option value="image/jpeg" label="JPEG" />
        <el-option value="image/png" label="PNG" />
        <el-option value="image/webp" label="WEBP" />
        <el-option value="image/gif" label="GIF" />
      </el-select>
      <el-select v-model="orderBy" placeholder="Sort By" style="width:180px" @change="load">
        <el-option value="created_at" label="Created Time" />
        <el-option value="id" label="ID" />
      </el-select>
      <el-select v-model="order" placeholder="Order" style="width:180px" @change="load">
        <el-option value="desc" label="Descending" />
        <el-option value="asc" label="Ascending" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="load">Refresh</el-button>
      <el-button @click="toggleSelectMode">Select</el-button>
    </div>
    <el-row :gutter="16" style="margin-top:12px">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in items" :key="item.id">
        <el-card shadow="hover" :class="['card', { selected: isSelected(item.id) }]" @click="cardClick(item.id)" @mousedown="onPressStart(item)" @mouseup="onPressEnd" @mouseleave="onPressEnd" @touchstart.passive="onPressStart(item)" @touchend.passive="onPressEnd">
          <div v-if="selectMode" class="selectbox">
            <el-checkbox :model-value="isSelected(item.id)" @change="() => toggleSelect(item.id)" />
          </div>
          <img class="thumb" :src="withJwtAbs(item.thumb_url)" alt="thumb" />
          <div class="meta">
            <div class="name">{{ item.original_filename }}</div>
            <div class="sub">ID: {{ item.id }} · {{ item.mime_type || 'unknown' }}</div>
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
    <el-dialog v-model="dialogVisible" title="Actions" width="420px" @close="onDialogClose">
      <div v-if="selectMode && selectedIds.length" class="dialog-actions">
        <div class="summary">Selected {{ selectedIds.length }} items</div>
        <el-button class="full" type="primary" @click="batchDownload">Download Selected</el-button>
        <el-button class="full" type="danger" @click="batchDelete">Delete Selected</el-button>
        <el-button class="full" @click="batchToggleFavorite">{{ status==='favorite' ? 'Unfavorite Selected' : 'Favorite Selected' }}</el-button>
      </div>
      <div v-else class="dialog-actions">
        <el-button class="full" type="primary" @click="selected && download(selected)" :disabled="!selected">Download</el-button>
        <el-button class="full" type="danger" @click="selected && remove(selected.id)" :disabled="!selected">Delete</el-button>
        <el-button class="full" @click="selected && toggleFavorite(selected)" :disabled="!selected">{{ selected?.is_favorite ? 'Unfavorite' : 'Favorite' }}</el-button>
      </div>
    </el-dialog>
    <el-empty v-if="!items.length && inited" description="No images. Upload images to get started." style="margin-top: 16px;" />
  </el-card>
</template>
<script setup lang="ts">
import api, { API_BASE } from '../api'
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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

const dialogVisible = ref(false)
const selected = ref<any | null>(null)
let pressTimer: any = null
const selectMode = ref(false)
const selectedIds = ref<number[]>([])
async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/images', { params: { page: page.value, page_size: pageSize.value, status: status.value, mime: mime.value, order_by: orderBy.value, order: order.value } })
    items.value = data.data.items || []
    total.value = data.data.total || 0
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Load failed')
  } finally {
    loading.value = false
    inited.value = true
  }
}

function cardClick(id: number) {
  if (dialogVisible.value) return
  if (selectMode.value) return toggleSelect(id)
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

async function remove(id: number) {
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this image? This action cannot be undone.', 'Confirm Delete', { type: 'warning' })
    await api.delete(`/files/${id}`)
    ElMessage.success('Image deleted successfully')
    load()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.message || 'Failed to delete image')
    }
  }
}

function onPressStart(item: any) {
  clearTimeout(pressTimer)
  pressTimer = setTimeout(() => {
    if (selectMode.value && selectedIds.value.length) {
      dialogVisible.value = true
    } else {
      selected.value = item; dialogVisible.value = true
    }
  }, 500)
}
function onPressEnd() {
  clearTimeout(pressTimer)
}
async function toggleFavorite(item: any) {
  try {
    if (item.is_favorite) {
      await api.delete(`/images/${item.id}/favorite`)
      item.is_favorite = false
      ElMessage.success('Removed from Favorites')
    } else {
      await api.post(`/images/${item.id}/favorite`)
      item.is_favorite = true
      ElMessage.success('Added to Favorites')
    }
    dialogVisible.value = false
    selected.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || 'Operation failed')
  }
}

function onDialogClose() {
  selected.value = null
}

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  selectedIds.value = []
  dialogVisible.value = false
  selected.value = null
}

function toggleSelect(id: number) {
  const i = selectedIds.value.indexOf(id)
  if (i >= 0) selectedIds.value.splice(i, 1)
  else selectedIds.value.push(id)
}

function isSelected(id: number) {
  return selectedIds.value.includes(id)
}

function findItem(id: number) {
  return items.value.find((x:any) => x.id === id)
}

function batchDownload() {
  for (const id of selectedIds.value) {
    const it = findItem(id)
    const url = it?.download_url || `/api/v1/files/${id}/download`
    setTimeout(() => window.open(withJwtAbs(url), '_blank'), 50)
  }
  dialogVisible.value = false
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`Delete ${selectedIds.value.length} selected images?`, 'Confirm Delete', { type: 'warning' })
    for (const id of selectedIds.value.slice()) {
      try { await api.delete(`/files/${id}`) } catch {}
    }
    ElMessage.success('Deleted selected images')
    selectedIds.value = []
    dialogVisible.value = false
    load()
  } catch {}
}

async function batchToggleFavorite() {
  try {
    const unfav = status.value === 'favorite'
    for (const id of selectedIds.value.slice()) {
      try {
        if (unfav) await api.delete(`/images/${id}/favorite`)
        else await api.post(`/images/${id}/favorite`)
      } catch {}
    }
    ElMessage.success(unfav ? 'Removed from Favorites' : 'Added to Favorites')
    dialogVisible.value = false
    selectedIds.value = []
    load()
  } catch {}
}

onMounted(load)
</script>
<style scoped>
.title { display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:8px; }
.toolbar { display:flex; gap:8px; align-items:center; margin-top:8px; flex-wrap:wrap; }
.toolbar :deep(.el-select) { width: 180px; }
.card { cursor:pointer; position: relative; }
.card.selected { border: 2px solid var(--el-color-primary); }
.selectbox { position:absolute; left:8px; top:8px; background: rgba(255,255,255,0.9); border-radius:6px; padding:2px 6px; }
.dialog-actions { display:flex; flex-direction: column; gap: 8px; width: 100%; }
.dialog-actions :deep(.el-button.full) { width: 100%; display:flex; justify-content: center; align-items: center; margin: 0; padding-left: 0; padding-right: 0; }
.thumb { width: 100%; height: 160px; object-fit: cover; border-radius: 4px; }
.meta { margin-top: 8px; }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sub { color: var(--el-text-color-secondary); font-size: 12px; }
.actions { display:flex; gap:8px; margin-top:8px; }
</style>
