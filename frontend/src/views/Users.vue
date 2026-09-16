<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span>用户列表</span>
        <el-button type="primary" size="small" @click="openCreate">+ 新增用户</el-button>
      </div>
    </template>
    <el-table :data="userList" size="small">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="display_name" label="显示名称" />
      <el-table-column label="角色">
        <template #default="{ row }"><el-tag v-if="row.role==='admin'" size="small" type="primary">管理员</el-tag><el-tag v-else size="small">普通用户</el-tag></template>
      </el-table-column>
      <el-table-column label="状态">
        <template #default="{ row }"><el-tag :type="row.status==='active'?'success':'danger'" size="small">{{ row.status === 'active' ? '启用' : '禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" text @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text :type="row.status==='active'?'danger':'primary'" @click="toggleStatus(row)">{{ row.status==='active'?'禁用':'启用' }}</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="480px">
    <el-form :model="form" label-width="80px">
      <el-form-item label="用户名" v-if="!isEdit">
        <el-input v-model="form.username" />
      </el-form-item>
      <el-form-item label="密码" v-if="!isEdit">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>
      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="form.role">
          <el-option label="普通用户" value="user" />
          <el-option label="管理员" value="admin" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveUser">{{ isEdit ? '保存' : '创建' }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '../api'

const userList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const form = ref({ username: '', password: '', display_name: '', email: '', role: 'user' })

async function loadData() {
  try {
    const res = await userApi.list()
    userList.value = res.data.data || []
  } catch {}
}

function openCreate() {
  isEdit.value = false
  editingId.value = null
  form.value = { username: '', password: '', display_name: '', email: '', role: 'user' }
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editingId.value = row.id
  form.value = { username: row.username, password: '', display_name: row.display_name || '', email: row.email || '', role: row.role }
  dialogVisible.value = true
}

async function saveUser() {
  try {
    if (isEdit.value) {
      await userApi.update(editingId.value, { display_name: form.value.display_name, email: form.value.email, role: form.value.role })
      ElMessage.success('更新成功')
    } else {
      await userApi.create({ username: form.value.username, password: form.value.password, display_name: form.value.display_name, email: form.value.email, role: form.value.role })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function toggleStatus(row) {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const msg = newStatus === 'disabled' ? '确定禁用该用户？' : '确定启用该用户？'
  try {
    await ElMessageBox.confirm(msg)
    await userApi.update(row.id, { status: newStatus })
    ElMessage.success(newStatus === 'disabled' ? '已禁用' : '已启用')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>
