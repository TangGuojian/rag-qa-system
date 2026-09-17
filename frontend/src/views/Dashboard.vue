<template>
  <div>
    <!-- 首次使用情况下面板全是 0，不给引导会很像「项目没跑起来」。
         这里把「接下来该干什么」直接摊开，全部完成后自动隐藏。 -->
    <el-card v-if="showGuide" shadow="never" class="start-guide">
      <template #header>
        <div class="guide-header">
          <span>开始使用：4 步完成第一次问答</span>
          <el-button text size="small" @click="guideDismissed = true">不再显示</el-button>
        </div>
      </template>
      <div class="guide-list">
        <div
          v-for="(s, i) in steps"
          :key="s.title"
          class="guide-item"
          :class="{ 'is-done': s.done, 'is-current': i === currentStep }"
        >
          <div class="guide-badge">{{ s.done ? '✓' : i + 1 }}</div>
          <div class="guide-text">
            <div class="guide-title">{{ s.title }}</div>
            <div class="guide-desc">{{ s.desc }}</div>
          </div>
          <el-button v-if="!s.done" size="small" :type="i === currentStep ? 'primary' : ''" plain @click="go(s.path)">
            {{ s.action }}
          </el-button>
          <span v-else class="guide-done">已完成</span>
        </div>
      </div>
    </el-card>

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
import { useRouter } from 'vue-router'
import { dashboardApi, aiApi } from '../api'

const router = useRouter()

const stats = ref([])
const trend = ref([])
const hotTopics = ref([])
const kbData = ref([])
const totalQa = ref(0)
const activeUsers = ref(0)
const apiCallsToday = ref(0)
const storageUsed = ref(0)
const aiStatus = ref({ has_key: false, supports_embedding: false })
const guideDismissed = ref(false)

const docCount = computed(() => kbData.value.reduce((s, k) => s + (k.doc_count || 0), 0))
const aiReady = computed(() => aiStatus.value.has_key && aiStatus.value.supports_embedding)

// 第 1 步的提示随配置状态变化：只配了对话、没有向量能力是最常见的卡点
const aiDesc = computed(() => {
  if (!aiStatus.value.has_key) {
    return '在「个人设置」里选择服务商，填入自己的 API Key'
  }
  if (!aiStatus.value.supports_embedding) {
    return '当前服务商不提供向量接口，请在「向量服务（可选）」单独配置一个（如硅基流动 BAAI/bge-m3），否则无法上传文档'
  }
  // 系统默认 Key 来自部署者，额度与他人共用；本项目提倡自带 Key（BYOK）
  if (!aiStatus.value.uses_user_key) {
    return '当前使用部署者的系统默认 Key；建议在「个人设置」配置自己的 Key，额度独立且不受他人影响'
  }
  return '对话与向量服务均已就绪'
})

const steps = computed(() => [
  {
    title: '配置 AI 服务',
    desc: aiDesc.value,
    done: aiReady.value,
    path: '/profile',
    action: '去配置',
  },
  {
    title: '新建知识库',
    desc: '知识库是文档的容器，没有它无法上传文档',
    done: kbData.value.length > 0,
    path: '/knowledge',
    action: '去新建',
  },
  {
    title: '上传文档',
    desc: '支持 PDF / Word / Excel / TXT，上传后自动分块并向量化',
    done: docCount.value > 0,
    path: '/knowledge',
    action: '去上传',
  },
  {
    title: '开始提问',
    desc: '勾选知识库提问，答案会附带参考来源与原文片段',
    done: totalQa.value > 0,
    path: '/qa',
    action: '去提问',
  },
])

const currentStep = computed(() => {
  const i = steps.value.findIndex(s => !s.done)
  return i === -1 ? null : i
})

const showGuide = computed(() => !guideDismissed.value && currentStep.value !== null)

function go(path) {
  router.push(path)
}

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

  // AI 配置状态单独取：即使上面的面板接口失败，也不该连引导一起消失
  try {
    const res = await aiApi.status()
    aiStatus.value = res.data || {}
  } catch {}
})
</script>

<style scoped>
.stat-num { font-size: 28px; font-weight: 700; color: #1677ff; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }

.start-guide { margin-bottom: 16px; }
.guide-header { display: flex; justify-content: space-between; align-items: center; }
.guide-list { display: flex; flex-direction: column; gap: 10px; }
.guide-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
.guide-item.is-current {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.guide-item.is-done { opacity: 0.75; }
.guide-badge {
  flex: none;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  font-size: 13px;
}
.guide-item.is-done .guide-badge { background: var(--el-color-success); }
.guide-text { flex: 1; min-width: 0; }
.guide-title { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); }
.guide-desc { font-size: 12px; line-height: 1.6; margin-top: 2px; color: var(--el-text-color-secondary); }
.guide-done { font-size: 12px; color: var(--el-color-success); }
</style>
