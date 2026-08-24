import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/change-password', component: () => import('../views/ChangePassword.vue') },
  { path: '/', component: () => import('../views/Dashboard.vue') },
  { path: '/transactions', component: () => import('../views/Transactions.vue') },
  { path: '/funders', component: () => import('../views/Funders.vue') },
  { path: '/activities', component: () => import('../views/Activities.vue') },
  { path: '/votes', component: () => import('../views/Votes.vue') },
  { path: '/votes/:id', component: () => import('../views/VoteDetail.vue') },
  { path: '/reports', component: () => import('../views/Reports.vue') },
  { path: '/users', component: () => import('../views/Users.vue') },
  { path: '/accounts', component: () => import('../views/Accounts.vue') },
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
