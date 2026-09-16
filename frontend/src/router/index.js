import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '工作台', admin: true } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('../views/KnowledgeBase.vue'), meta: { title: '知识库管理', admin: true } },
      { path: 'qa', name: 'QA', component: () => import('../views/QA.vue'), meta: { title: '智能问答' } },
      { path: 'history', name: 'History', component: () => import('../views/History.vue'), meta: { title: '问答历史' } },
      { path: 'profile', name: 'Profile', component: () => import('../views/Profile.vue'), meta: { title: '个人设置' } },
      { path: 'graph', name: 'Graph', component: () => import('../views/Graph.vue'), meta: { title: '知识图谱', admin: true } },
      { path: 'users', name: 'Users', component: () => import('../views/Users.vue'), meta: { title: '用户管理', admin: true } },
      { path: 'config', name: 'Config', component: () => import('../views/Config.vue'), meta: { title: '系统配置', admin: true } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }
  if (to.meta.admin && localStorage.getItem('role') !== 'admin') {
    return next('/qa')
  }
  next()
})

export default router
