import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { title: '登录', plain: true } },
  { path: '/change-password', component: () => import('../views/ChangePassword.vue'), meta: { title: '修改密码', plain: true } },
  { path: '/', component: () => import('../views/Dashboard.vue'), meta: { title: '首页' } },
  { path: '/transactions', component: () => import('../views/Transactions.vue'), meta: { title: '记账' } },
  { path: '/funders', component: () => import('../views/Funders.vue'), meta: { title: '缴款人' } },
  { path: '/activities', component: () => import('../views/Activities.vue'), meta: { title: '活动管理' } },
  { path: '/votes', component: () => import('../views/Votes.vue'), meta: { title: '投票' } },
  { path: '/votes/:id', component: () => import('../views/VoteDetail.vue'), meta: { title: '投票详情', hidden: true } },
  { path: '/reports', component: () => import('../views/Reports.vue'), meta: { title: '报表下载' } },
  { path: '/users', component: () => import('../views/Users.vue'), meta: { title: '账号管理' } },
  { path: '/accounts', component: () => import('../views/Accounts.vue'), meta: { title: '科目管理' } },
  { path: '/data', component: () => import('../views/DataManage.vue'), meta: { title: '数据管理' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.token) {
    return '/login'
  }
  // 需强制改密的账号，先跳转改密页
  if (auth.mustChangePassword && to.path !== '/change-password') {
    return '/change-password'
  }
  return true
})

export default router
