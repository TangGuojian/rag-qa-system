<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>知识库列表</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">+ 新建知识库</el-button>
        </div>
      </template>
      <el-table :data="kbList" size="small">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="doc_count" label="文档数" />
        <el-table-column prop="chunk_count" label="向量数" />
        <el-table-column prop="graph_node_count" label="图谱节点" />
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" text @click="editKb(row)">编辑</el-button>
            <el-button size="small" text type="danger" @click="deleteKb(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-card style="margin-top:16px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>文档管理</span>
          <div>
            <el-button type="primary" size="small" @click="showUpload = true">+ 上传文档</el-button>
          </div>
        </div>
      </template>
      <el-table :data="docList" size="small">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="file_size" label="大小" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tooltip v-if="row.error_msg" :content="row.error_msg" placement="top" :show-after="200">
              <el-tag :type="statusType(row.status)" size="small" style="cursor:help">
                {{ statusLabel(row.status) }} ?
              </el-tag>
            </el-tooltip>
            <el-tag v-else :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" />
        <el-table-column prop="created_at" label="上传时间" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" text @click="downloadDoc(row)">下载</el-button>
            <el-button size="small" text type="danger" @click="deleteDoc(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="新建知识库" width="400px">
      <el-form :model="kbForm">
        <el-form-item label="名称"><el-input v-model="kbForm.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="kbForm.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreateDialog=false">取消</el-button><el-button type="primary" @click="createKb">确定</el-button></template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑知识库" width="400px">
      <el-form :model="editForm">
        <el-form-item label="名称"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showEditDialog=false">取消</el-button><el-button type="primary" @click="confirmEditKb">确定</el-button></template>
    </el-dialog>

    <el-dialog v-model="showUpload" title="上传文档" width="500px" :close-on-click-modal="false">
      <el-form>
        <el-form-item label="知识库">
          <el-select v-model="uploadKbId" style="width:100%">
            <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            multiple
            :on-change="onFileChange"
            :file-list="uploadFiles"
          >
            <el-button size="small">选择文件</el-button>
            <template #tip><div style="font-size:12px;color:#999;margin-top:4px">支持 PDF / DOCX / MD / XLSX / TXT / CSV</div></template>
          </el-upload>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="uploadTags" placeholder="可选，逗号分隔" />
        </el-form-item>
      </el-form>
      <div v-if="uploading" style="text-align:center;padding:12px">
        <el-progress :percentage="uploadProgress" :stroke-width="6" />
        <div style="font-size:12px;color:#999;margin-top:4px">正在上传解析中...</div>
      </div>
      <template #footer>
        <el-button @click="closeUpload">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :disabled="!uploadFiles.length || !uploadKbId || uploading">开始上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { kbApi, docApi } from '../api'

const kbList = ref([])
const docList = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showUpload = ref(false)
const kbForm = ref({ name: '', description: '' })
const editForm = ref({ name: '', description: '' })
const editKbId = ref(null)
const uploadKbId = ref(null)
const uploadTags = ref('')
const uploadFiles = ref([])
const uploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)

function statusType(s) {
  return { pending: 'info', parsing: 'warning', vectorizing: 'warning', completed: 'success', failed: 'danger' }[s] || 'info'
}

function statusLabel(s) {
  const labels = { pending: '待处理', parsing: '解析中', vectorizing: '索引中', completed: '已完成', failed: '失败' }
  return labels[s] || s
}

function onFileChange(uploadFile) {
  uploadFiles.value = uploadRef.value.uploadFiles
}

async function loadData() {
  try {
    const [kbRes, docRes] = await Promise.all([kbApi.list(), docApi.list()])
    kbList.value = kbRes.data || []
    docList.value = docRes.data || []
  } catch {
    ElMessage.error('加载数据失败')
  }
}

async function createKb() {
  try {
    await kbApi.create(kbForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    kbForm.value = { name: '', description: '' }
    loadData()
  } catch {
    ElMessage.error('创建失败')
  }
}

function editKb(row) {
  editKbId.value = row.id
  editForm.value = { name: row.name, description: row.description || '' }
  showEditDialog.value = true
}

async function confirmEditKb() {
  try {
    await kbApi.update(editKbId.value, editForm.value)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    loadData()
  } catch {
    ElMessage.error('更新失败')
  }
}

async function deleteKb(row) {
  try {
    await ElMessageBox.confirm('确定删除该知识库？')
    await kbApi.delete(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch {
    ElMessage.error('删除失败')
  }
}

function closeUpload() {
  showUpload.value = false
  uploadFiles.value = []
  uploadTags.value = ''
  uploadKbId.value = null
  uploadProgress.value = 0
  uploading.value = false
}

async function confirmUpload() {
  if (!uploadFiles.value.length || !uploadKbId.value) return
  uploading.value = true
  uploadProgress.value = 10

  let success = 0
  let fail = 0
  const failures = []
  const total = uploadFiles.value.length

  for (let i = 0; i < total; i++) {
    const item = uploadFiles.value[i]
    const f = item.raw || item
    const name = f.name || `文件${i + 1}`
    const formData = new FormData()
    formData.append('file', f)
    formData.append('kb_id', uploadKbId.value)
    if (uploadTags.value.trim()) {
      formData.append('tags', uploadTags.value.trim())
    }
    try {
      // 注意：接口返回 201 只代表「请求被受理」，文档可能仍在索引中甚至已失败，
      // 必须看响应体里的 status 才能判断真实结果。
      const res = await docApi.upload(formData)
      const data = res.data || {}
      if (data.status === 'completed') {
        success++
      } else {
        fail++
        failures.push(`${name}：${data.error_msg || '未能完成索引'}`)
      }
    } catch (err) {
      fail++
      const detail = err?.response?.data?.detail
      failures.push(`${name}：${typeof detail === 'string' ? detail : '请求失败'}`)
    }
    uploadProgress.value = Math.round(((i + 1) / total) * 90) + 10
  }

  uploadProgress.value = 100
  closeUpload()
  loadData()

  if (fail === 0) {
    ElMessage.success(`上传完成：${success} 个文档已索引`)
  } else {
    // 失败原因通常较长且需要复制排查，消息条一闪而过看不全，改用弹窗
    ElMessageBox.alert(
      `<div style="line-height:1.7">${failures.map(x => `• ${escapeHtml(x)}`).join('<br/>')}</div>`,
      `上传完成：${success} 成功，${fail} 失败`,
      { dangerouslyUseHTMLString: true, confirmButtonText: '我知道了' }
    ).catch(() => {})
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ))
}

async function downloadDoc(row) {
  try {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const token = localStorage.getItem('token')
    const resp = await fetch(`${base}/documents/${row.id}/download`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!resp.ok) throw new Error('下载失败')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

async function deleteDoc(row) {
  await ElMessageBox.confirm('确定删除该文档？')
  await docApi.delete(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>
