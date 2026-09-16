<template>
  <div class="login-page">
    <div class="login-card">
      <h1>智能问答系统</h1>
      <p>企业知识库 · 智能问答平台</p>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">登 录</el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('admin')
const password = ref('admin123')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    ElMessage.success('登录成功')
    router.push(auth.isAdmin() ? '/dashboard' : '/qa')
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { display: flex; align-items: center; justify-content: center; height: 100vh; background: linear-gradient(135deg, #667eea, #764ba2); }
.login-card { width: 400px; padding: 40px; background: #fff; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,.1); }
.login-card h1 { text-align: center; margin-bottom: 8px; font-size: 24px; }
.login-card p { text-align: center; color: #999; margin-bottom: 32px; font-size: 14px; }
</style>
