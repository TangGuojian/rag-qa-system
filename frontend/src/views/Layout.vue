<template>
  <el-container style="height:100vh">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <div class="logo-icon">AI</div>
        <span>智能问答系统</span>
      </div>
      <el-menu :router="true" :default-active="route.path" background-color="#001529" text-color="#ffffffa6" active-text-color="#fff">
        <el-menu-item index="/dashboard" v-if="auth.isAdmin()">
          <el-icon><Monitor /></el-icon><span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/knowledge" v-if="auth.isAdmin()">
          <el-icon><Folder /></el-icon><span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/qa">
          <el-icon><ChatDotSquare /></el-icon><span>智能问答</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Document /></el-icon><span>问答历史</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon><span>个人设置</span>
        </el-menu-item>
        <el-menu-item index="/graph" v-if="auth.isAdmin()">
          <el-icon><Share /></el-icon><span>知识图谱</span>
        </el-menu-item>
        <el-menu-item index="/users" v-if="auth.isAdmin()">
          <el-icon><User /></el-icon><span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/config" v-if="auth.isAdmin()">
          <el-icon><Setting /></el-icon><span>系统配置</span>
        </el-menu-item>
      </el-menu>
      <div class="user-info">
        <el-avatar size="small">{{ auth.role?.charAt(0).toUpperCase() }}</el-avatar>
        <span>{{ auth.isAdmin() ? '管理员' : '普通用户' }}</span>
        <el-button text style="color:#ffffffa6;margin-left:auto" @click="handleLogout">退出</el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <h2>{{ route.meta.title }}</h2>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { Monitor, Folder, ChatDotSquare, Document, Share, User, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar { background: #001529; display: flex; flex-direction: column; overflow: hidden; }
.logo { padding: 20px 16px; font-size: 18px; font-weight: 700; color: #fff; border-bottom: 1px solid #ffffff1a; display: flex; align-items: center; gap: 10px; }
.logo-icon { width: 32px; height: 32px; background: #1677ff; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.el-menu { border-right: none; }
.user-info { padding: 16px 20px; border-top: 1px solid #ffffff1a; display: flex; align-items: center; gap: 10px; color: #fff; font-size: 13px; }
.header { background: #fff; border-bottom: 1px solid #e8e8e8; display: flex; align-items: center; height: 56px; padding: 0 24px; }
.header h2 { font-size: 16px; font-weight: 600; }
.main-content { background: #f5f5f5; padding: 20px; overflow-y: auto; }
</style>
