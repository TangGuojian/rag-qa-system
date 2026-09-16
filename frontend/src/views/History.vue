<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span>问答历史</span>
      </div>
    </template>
    <div style="display:flex;gap:8px;margin-bottom:16px">
      <el-input v-model="search" placeholder="搜索提问内容..." style="max-width:300px" clearable />
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
      <el-button type="primary" @click="loadData">搜索</el-button>
    </div>
    <el-table :data="list" size="small">
      <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="时间" width="160" />
      <el-table-column label="反馈" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.useful === true" size="small" type="success">有用</el-tag>
          <el-tag v-else-if="row.useful === false" size="small" type="danger">无用</el-tag>
          <span v-else style="color:#999">未反馈</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" text @click="viewDetail(row)">查看</el-button>
          <el-button size="small" text type="danger" @click="deleteRow(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total > 0" v-model:current-page="page" :page-size="size" :total="total" layout="prev, pager, next" style="margin-top:16px;justify-content:center" @current-change="loadData" />
  </el-card>

  <el-dialog v-model="detailVisible" title="问答详情" width="720px">
    <div v-if="detail">
      <h4 style="margin-bottom:8px">问题</h4>
      <p style="background:#f5f7fa;padding:12px;border-radius:6px;margin-bottom:16px">{{ detail.question }}</p>

      <h4 style="margin-bottom:8px">答案</h4>
      <div style="background:#f5f7fa;padding:12px;border-radius:6px;margin-bottom:16px;white-space:pre-wrap;line-height:1.6">{{ detail.answer }}</div>

      <h4 style="margin-bottom:8px">反馈</h4>
      <p style="margin-bottom:16px">
        <el-tag v-if="detail.useful === true" type="success">有用</el-tag>
        <el-tag v-else-if="detail.useful === false" type="danger">无用</el-tag>
        <span v-else style="color:#999">未反馈</span>
      </p>

      <h4 style="margin-bottom:8px">时间</h4>
      <p style="margin-bottom:16px;color:#666;font-size:13px">{{ detail.created_at }}</p>
    </div>
    <template #footer>
      <el-button @click="detailVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { historyApi } from '../api'

const list = ref([])
const search = ref('')
const dateRange = ref(null)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const detailVisible = ref(false)
const detail = ref(null)

async function loadData() {
  try {
    const params = { page: page.value, size: size.value }
    if (search.value) params.keyword = search.value
    if (dateRange.value) {
      params.date_from = dateRange.value[0].toISOString().split('T')[0]
      params.date_to = dateRange.value[1].toISOString().split('T')[0]
    }
    const res = await historyApi.list(params)
    list.value = res.data.data || []
    total.value = res.data.total || 0
  } catch {}
}
function viewDetail(row) {
  detail.value = row
  detailVisible.value = true
}
async function deleteRow(row) {
  try {
    await ElMessageBox.confirm('确定删除？')
    await historyApi.delete(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch {}
}
onMounted(loadData)
</script>
