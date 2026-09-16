<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span>系统配置</span>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
      </div>
    </template>
    <el-form label-width="120px">
      <el-divider content-position="left">LLM 参数</el-divider>
      <el-form-item label="模型选择"><el-select v-model="config.llm_model"><el-option label="qwen3.7-plus" value="qwen3.7-plus" /><el-option label="gpt-4o" value="gpt-4o" /></el-select></el-form-item>
      <el-form-item label="温度"><el-input-number v-model="config.temperature" :min="0" :max="2" :step="0.1" /></el-form-item>
      <el-form-item label="最大 Token"><el-input-number v-model="config.max_tokens" :min="128" :max="8192" :step="128" /></el-form-item>

      <el-divider content-position="left">解析策略</el-divider>
      <el-form-item label="分块大小"><el-input-number v-model="config.chunk_size" :min="128" :max="2048" :step="64" /></el-form-item>
      <el-form-item label="重叠大小"><el-input-number v-model="config.chunk_overlap" :min="0" :max="512" :step="16" /></el-form-item>

      <el-divider content-position="left">检索配置</el-divider>
      <el-form-item label="检索方式"><el-select v-model="config.retrieval_mode"><el-option label="混合检索" value="hybrid" /><el-option label="向量检索" value="vector" /><el-option label="关键词检索" value="keyword" /></el-select></el-form-item>
      <el-form-item label="召回数量 (Top-K)"><el-input-number v-model="config.top_k" :min="1" :max="20" /></el-form-item>
      <el-form-item label="相似度阈值"><el-input-number v-model="config.threshold" :min="0" :max="1" :step="0.05" /></el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi } from '../api'

const config = ref({
  llm_model: 'qwen3.7-plus', temperature: 0.7, max_tokens: 4096,
  chunk_size: 512, chunk_overlap: 64,
  retrieval_mode: 'hybrid', top_k: 5, threshold: 0.75,
})

onMounted(async () => {
  try {
    const res = await configApi.get()
    Object.assign(config.value, res.data)
  } catch {}
})

async function saveConfig() {
  try {
    await configApi.update(config.value)
    ElMessage.success('配置已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}
</script>
