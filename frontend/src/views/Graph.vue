<template>
  <div>
    <div style="display:flex;justify-content:space-between;margin-bottom:16px">
      <div>
        <el-button type="primary" @click="buildGraph">▶ 手动构建</el-button>
        <el-button @click="loadData">🔄 刷新</el-button>
      </div>
      <el-input v-model="searchText" placeholder="搜索实体..." style="max-width:200px" clearable @input="filterNodes" />
    </div>
    <el-card>
      <template #header>知识图谱可视化</template>
      <div ref="chartRef" style="width:100%;height:500px"></div>
    </el-card>
    <el-card style="margin-top:16px">
      <template #header>实体列表 ({{ filteredNodes.length }}/{{ nodes.length }})</template>
      <el-table :data="filteredNodes" size="small">
        <el-table-column prop="name" label="实体名称" />
        <el-table-column prop="label" label="类型" />
        <el-table-column prop="doc_num" label="文号" />
        <el-table-column label="关联数">
          <template #default="{ row }">
            {{ edgeCountByNode(row.id) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { graphApi } from '../api'
import * as echarts from 'echarts'

const searchText = ref('')
const chartRef = ref(null)
const nodes = ref([])
const edges = ref([])
const filteredNodes = ref([])
const filteredEdges = ref([])
let chart = null

function filterNodes() {
  const q = searchText.value.toLowerCase()
  if (!q) {
    filteredNodes.value = nodes.value
    filteredEdges.value = edges.value
  } else {
    const matched = nodes.value.filter(n => (n.name || '').toLowerCase().includes(q))
    const matchedIds = new Set(matched.map(n => n.id))
    const connEdges = edges.value.filter(e =>
      matchedIds.has(e.source) || matchedIds.has(e.target)
    )
    const neighborIds = new Set()
    connEdges.forEach(e => { neighborIds.add(e.source); neighborIds.add(e.target) })
    filteredNodes.value = nodes.value.filter(n => neighborIds.has(n.id))
    filteredEdges.value = connEdges
  }
  renderChart()
}

function edgeCountByNode(nodeId) {
  return edges.value.filter(e => e.source === nodeId || e.target === nodeId).length
}

function renderChart() {
  nextTick(() => {
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value)
    const totalNodes = nodes.value.length
    const shownNodes = filteredNodes.value.length
    const titleText = searchText.value
      ? `知识图谱 (筛选 ${shownNodes}/${totalNodes} 节点)`
      : `知识图谱 (共 ${totalNodes} 节点)`
    chart.setOption({
      title: { text: titleText, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: {},
      series: [{
        type: 'graph',
        layout: 'force',
        force: { repulsion: 300, edgeLength: 100 },
        roam: true,
        draggable: true,
        data: filteredNodes.value.map(n => ({
          id: n.id,
          name: n.name || n.label,
          category: n.label,
          symbolSize: n.label === 'Agency' ? 30 : n.label === 'Category' ? 25 : 20,
          itemStyle: {
            color: n.label === 'Agency' ? '#f56c6c' : n.label === 'Category' ? '#67c23a' : '#409eff'
          }
        })),
        links: filteredEdges.value.map(e => ({
          source: e.source,
          target: e.target,
          label: { show: true, formatter: e.label }
        })),
        categories: [
          { name: 'Agency', itemStyle: { color: '#f56c6c' } },
          { name: 'Category', itemStyle: { color: '#67c23a' } },
          { name: 'Document', itemStyle: { color: '#409eff' } },
          { name: 'DocNumber', itemStyle: { color: '#909399' } },
        ],
        label: { show: true, position: 'right', fontSize: 10 },
        lineStyle: { color: 'source', curveness: 0.3, opacity: 0.5 },
      }]
    })
    chart.resize()
  })
}

async function loadData() {
  try {
    const res = await graphApi.data()
    nodes.value = res.data.nodes || []
    edges.value = res.data.edges || []
    filteredNodes.value = nodes.value
    filteredEdges.value = edges.value
    renderChart()
  } catch (e) {
    ElMessage.error('加载图谱数据失败')
  }
}

async function buildGraph() {
  try {
    await graphApi.build()
    ElMessage.success('图谱构建任务已触发')
    setTimeout(loadData, 1000)
  } catch {}
}

onMounted(loadData)
</script>
