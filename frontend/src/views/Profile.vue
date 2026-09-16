<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span>个人设置</span>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </div>
    </template>
    <el-form label-width="120px" v-if="form">
      <el-divider content-position="left">基本信息</el-divider>
      <el-form-item label="用户名">{{ form.username }}</el-form-item>
      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" placeholder="选填" />
      </el-form-item>
      <el-divider content-position="left">API Key 设置</el-divider>
      <el-form-item label="API Key">
        <el-input v-model="form.api_key" type="password" show-password placeholder="输入你的 Dashscope API Key" />
      </el-form-item>
      <el-form-item>
        <template #label>状态</template>
        <el-tag :type="hasCustomKey ? 'success' : 'info'" size="small">
          {{ hasCustomKey ? '使用自定义 Key' : '使用系统默认 Key' }}
        </el-tag>
      </el-form-item>
      <el-form-item>
        <span style="color:#999;font-size:12px">设置后，问答时将使用你的 API Key 调用 AI 服务。留空则使用系统默认 Key。</span>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '../api'

import { computed } from 'vue'

const form = ref(null)

const hasCustomKey = computed(() => !!form.value?.api_key)

onMounted(async () => {
  try {
    const res = await userApi.getProfile()
    form.value = { ...res.data }
  } catch {
    ElMessage.error('加载个人信息失败')
  }
})

async function saveProfile() {
  try {
    await userApi.updateProfile({
      display_name: form.value.display_name,
      api_key: form.value.api_key || null,
    })
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  }
}
</script>