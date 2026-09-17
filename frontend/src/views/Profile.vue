<template>
  <el-card v-loading="loading">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span>个人设置</span>
        <div>
          <el-button :loading="testing" @click="testConnection">测试连接</el-button>
          <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
        </div>
      </div>
    </template>

    <el-form label-width="130px" v-if="form">
      <el-divider content-position="left">基本信息</el-divider>
      <el-form-item label="用户名">{{ form.username }}</el-form-item>
      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" placeholder="选填" style="max-width:320px" />
      </el-form-item>

      <el-divider content-position="left">AI 服务配置</el-divider>

      <el-alert
        v-if="!form.api_key"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom:18px"
        title="尚未配置 API Key"
        description="本项目不内置任何 Key：请在下方选择服务商并填入你自己的 API Key，保存后即可正常提问。没有 Key 时可先参考 README 的「Key 从哪来」一节申请。"
      />

      <el-form-item label="服务商">
        <el-select
          v-model="providerId"
          placeholder="请选择服务商"
          style="max-width:420px"
          @change="onProviderChange"
        >
          <el-option
            v-for="p in providers"
            :key="p.id"
            :label="p.label"
            :value="p.id"
          />
        </el-select>
        <el-link
          v-if="currentProvider && currentProvider.key_url"
          :href="currentProvider.key_url"
          target="_blank"
          type="primary"
          style="margin-left:12px"
        >
          去申请 Key
        </el-link>
      </el-form-item>

      <el-form-item v-if="currentProvider && currentProvider.note">
        <span style="color:#909399;font-size:12px">{{ currentProvider.note }}</span>
      </el-form-item>

      <el-form-item label="API Key">
        <el-input
          v-model="form.api_key"
          type="password"
          show-password
          placeholder="粘贴你的 API Key（保存后仅自己可见）"
          style="max-width:520px"
        />
      </el-form-item>

      <el-form-item label="API 地址">
        <el-input
          v-model="form.api_base"
          placeholder="https://..."
          style="max-width:520px"
        />
        <div style="color:#909399;font-size:12px;margin-top:4px">
          兼容 OpenAI 协议的地址。选服务商时会自动填充，也可手动修改为自建网关。
        </div>
      </el-form-item>

      <el-form-item label="对话模型">
        <el-input v-model="form.llm_model" placeholder="例如 qwen3.7-plus" style="max-width:520px">
          <template #append>
            <el-button :loading="loadingModels" @click="openModelPicker('llm')">获取可用模型</el-button>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="向量模型">
        <el-input v-model="form.embedding_model" placeholder="例如 text-embedding-v3" style="max-width:520px">
          <template #append>
            <el-button :loading="loadingModels" @click="openModelPicker('embedding')">获取可用模型</el-button>
          </template>
        </el-input>
        <div
          v-if="currentProvider && !currentProvider.supports_embedding"
          style="color:#e6a23c;font-size:12px;margin-top:4px"
        >
          该服务商不提供向量化接口，请另外配置一个支持向量的服务商（例如硅基流动），否则文档无法入库。
        </div>
      </el-form-item>

      <el-form-item label="当前生效">
        <div v-if="status" style="font-size:12px;color:#606266;line-height:1.9">
          <div>Key：{{ status.api_key_masked || '未配置' }}</div>
          <div>地址：{{ status.api_base || '-' }}</div>
          <div>对话模型：{{ status.llm_model || '-' }}</div>
          <div>向量模型：{{ status.embedding_model || '-' }}</div>
        </div>
      </el-form-item>

      <el-form-item v-if="testResult" label="连接测试">
        <div style="font-size:13px;line-height:1.9">
          <div>
            <el-tag :type="testResult.chat && testResult.chat.ok ? 'success' : 'danger'" size="small">
              对话
            </el-tag>
            <span style="margin-left:8px;color:#606266">
              {{ testResult.chat ? testResult.chat.message : '-' }}
            </span>
          </div>
          <div>
            <el-tag :type="testResult.embedding && testResult.embedding.ok ? 'success' : 'danger'" size="small">
              向量
            </el-tag>
            <span style="margin-left:8px;color:#606266">
              {{ testResult.embedding ? testResult.embedding.message : '-' }}
            </span>
          </div>
        </div>
      </el-form-item>
    </el-form>
  </el-card>

  <!-- 模型选择弹窗：直接向服务商拉取真实列表，避免手写模型名出错 -->
  <el-dialog v-model="modelDialog" :title="modelDialogTitle" width="560px">
    <div v-if="!modelList.length" style="color:#909399;font-size:13px">
      {{ modelMessage || '暂无数据' }}
    </div>
    <div v-else>
      <el-input v-model="modelKeyword" placeholder="搜索模型名" clearable style="margin-bottom:10px" />
      <div style="max-height:360px;overflow:auto">
        <div
          v-for="m in filteredModels"
          :key="m"
          class="model-item"
          @click="pickModel(m)"
        >
          {{ m }}
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="modelDialog = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi, aiApi } from '../api'

const form = ref(null)
const providers = ref([])
const providerId = ref('')
const status = ref(null)
const testResult = ref(null)

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

const modelDialog = ref(false)
const modelDialogTitle = ref('')
const modelList = ref([])
const modelMessage = ref('')
const modelKeyword = ref('')
const modelTarget = ref('llm')
const loadingModels = ref(false)

const currentProvider = computed(
  () => providers.value.find((p) => p.id === providerId.value) || null
)

const filteredModels = computed(() => {
  const kw = modelKeyword.value.trim().toLowerCase()
  if (!kw) return modelList.value
  return modelList.value.filter((m) => m.toLowerCase().includes(kw))
})

onMounted(async () => {
  loading.value = true
  try {
    const [profileRes, providerRes] = await Promise.all([
      userApi.getProfile(),
      aiApi.providers(),
    ])
    form.value = { ...profileRes.data }
    providers.value = providerRes.data?.data || providerRes.data || []
    providerId.value = guessProvider(form.value.api_base)
    await loadStatus()
  } catch {
    ElMessage.error('加载个人信息失败')
  } finally {
    loading.value = false
  }
})

function guessProvider(apiBase) {
  if (!apiBase) return ''
  const hit = providers.value.find((p) => p.api_base && p.api_base === apiBase)
  return hit ? hit.id : 'custom'
}

function onProviderChange(id) {
  const p = providers.value.find((x) => x.id === id)
  if (!p) return
  if (p.id === 'custom') {
    // 自定义不清空，避免误删已填内容
    return
  }
  form.value.api_base = p.api_base
  form.value.llm_model = p.llm_model || form.value.llm_model
  form.value.embedding_model = p.embedding_model || form.value.embedding_model
}

async function loadStatus() {
  try {
    const res = await aiApi.status()
    status.value = res.data
  } catch {
    status.value = null
  }
}

async function saveProfile() {
  saving.value = true
  try {
    await userApi.updateProfile({
      display_name: form.value.display_name,
      api_key: form.value.api_key || null,
      api_base: form.value.api_base || null,
      llm_model: form.value.llm_model || null,
      embedding_model: form.value.embedding_model || null,
    })
    ElMessage.success('保存成功')
    await loadStatus()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const res = await aiApi.test({
      api_key: form.value.api_key || null,
      api_base: form.value.api_base || null,
      llm_model: form.value.llm_model || null,
      embedding_model: form.value.embedding_model || null,
    })
    testResult.value = res.data
    if (res.data.ok) {
      ElMessage.success('连接正常，可以开始提问了')
    } else {
      ElMessage.warning('连接未通过，请看下方提示')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '测试失败')
  } finally {
    testing.value = false
  }
}

async function openModelPicker(target) {
  if (!form.value.api_key) {
    ElMessage.warning('请先填写 API Key 并保存，再获取模型列表')
    return
  }
  modelTarget.value = target
  modelDialogTitle.value = target === 'llm' ? '选择对话模型' : '选择向量模型'
  modelKeyword.value = ''
  modelList.value = []
  modelMessage.value = ''
  modelDialog.value = true
  loadingModels.value = true
  try {
    const res = await aiApi.models({
      api_key: form.value.api_key || null,
      api_base: form.value.api_base || null,
    })
    const data = res.data
    if (data.ok) {
      modelList.value = data.models || []
    } else {
      modelMessage.value = data.message || '获取失败'
    }
  } catch (e) {
    modelMessage.value = e?.response?.data?.detail || '获取失败'
  } finally {
    loadingModels.value = false
  }
}

function pickModel(name) {
  if (modelTarget.value === 'llm') {
    form.value.llm_model = name
  } else {
    form.value.embedding_model = name
  }
  modelDialog.value = false
  ElMessage.success(`已选择 ${name}，记得点「保存」`)
}
</script>

<style scoped>
.model-item {
  padding: 8px 10px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
  color: #303133;
}
.model-item:hover {
  background: #f0f7ff;
  color: #409eff;
}
</style>
