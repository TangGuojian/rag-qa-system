<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover"><div class="stat-num">{{ stat.value }}</div><div class="stat-label">{{ stat.label }}</div></el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="16">
        <el-card>
          <template #header>问答趋势（近7日）</template>
          <div style="height:220px;display:flex;align-items:center;justify-content:center;color:#999" v-if="trend.length === 0">暂无数据</div>
          <div style="height:220px;padding:8px" v-else>
            <div v-for="t in trend" :key="t.date" style="display:flex;align-items:center;margin:8px 0;gap:8px">
              <span style="width:80px;font-size:12px;color:#666">{{ t.date.slice(5) }}</span>
              <div style="flex:1;height:20px;background:#f0f0f0;border-radius:4px;overflow:hidden">
                <div :style="{width: (t.count / maxTrend * 100) + '%', height:'100%', background:'#1677ff', borderRadius:'4px', minWidth: t.count > 0 ? '4px' : 0}"></div>
              </div>
              <span style="width:30px;text-align:right;font-size:12px">{{ t.count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card><template #header>系统运行状态</template>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item label="存储使用量">{{ storageLabel }}</el-descriptions-item>
            <el-descriptions-item label="API 今日调用">{{ apiCallsToday }} 次</el-descriptions-item>
            <el-descriptions-item label="总问答次数">{{ totalQa }} 次</el-descriptions-item>
            <el-descriptions-item label="活跃用户数">{{ activeUsers }} 人</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card style="margin-top:12px"><template #header>热点推荐</template>
          <el-tag v-for="t in hotTopics" :key="t.name" :style="{fontSize:t.size+'px'}" style="margin:4px">{{ t.name }}</el-tag>
          <span v-if="hotTopics.length === 0" style="color:#999;font-size:13px">暂无数据</span>
        </el-card>
      </el-col>
    </el-row>
    <el-card style="margin-top:16px"><template #header>知识库概览</template>
      <el-table :data="kbData" size="small">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="doc_count" label="文档数" />
        <el-table-column prop="parsed" label="已解析" />
        <el-table-column prop="vectorized" label="已向量化" />
        <el-table-column prop="nodes" label="图谱节点" />
        <el-table-column prop="edges" label="图谱关系" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi } from '../api'

const stats = ref([])
const trend = ref([])
const hotTopics = ref([])
const kbData = ref([])
const totalQa = ref(0)
const activeUsers = ref(0)
const apiCallsToday = ref(0)
const storageUsed = ref(0)

const maxTrend = computed(() => Math.max(1, ...trend.value.map(t => t.count)))
const storageLabel = computed(() => {
  const s = storageUsed.value
  if (s < 1024) return s + ' B'
  if (s < 1024 * 1024) return (s / 1024).toFixed(1) + ' KB'
  if (s < 1024 * 1024 * 1024) return (s / 1024 / 1024).toFixed(1) + ' MB'
  return (s / 1024 / 1024 / 1024).toFixed(2) + ' GB'
})

onMounted(async () => {
  try {
    const [kbRes, qaRes, statusRes, hotRes] = await Promise.all([
      dashboardApi.kbOverview(),
      dashboardApi.qaStats(),
      dashboardApi.systemStatus(),
      dashboardApi.hotTopics(),
    ])
    kbData.value = kbRes.data || []
    totalQa.value = qaRes.data.total_qa || 0
    activeUsers.value = qaRes.data.active_users || 0
    trend.value = qaRes.data.trend || []
    storageUsed.value = statusRes.data.storage_used || 0
    apiCallsToday.value = statusRes.data.api_calls_today || 0
    hotTopics.value = hotRes.data || []

    stats.value = [
      { label: '知识库总数', value: kbData.value.length },
      { label: '文档总数', value: kbData.value.reduce((s, k) => s + k.doc_count, 0) },
      { label: '总问答次数', value: totalQa.value },
      { label: '活跃用户数', value: activeUsers.value },
    ]
  } catch {}
})
</script>

<style scoped>
.stat-num { font-size: 28px; font-weight: 700; color: #1677ff; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
</style>
