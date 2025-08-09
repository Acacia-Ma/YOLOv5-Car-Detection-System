import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载
const Home = () => import('../views/Home.vue')
const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const History = () => import('../views/History.vue')
const Admin = () => import('../views/Admin.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/history',
    name: 'History',
    component: History,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem('username')
  const userInfo = localStorage.getItem('userInfo')
  
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 需要登录的路由
    if (!isLoggedIn) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      // 检查是否需要管理员权限
      if (to.matched.some(record => record.meta.requiresAdmin)) {
        if (!userInfo) {
          next({ path: '/login' })
          return
        }
        
        const user = JSON.parse(userInfo)
        if (user.role !== 'admin') {
          next({ path: '/' })
          return
        }
      }
      next()
    }
  } else {
    // 不需要登录的路由
    if (isLoggedIn && (to.path === '/login' || to.path === '/register')) {
      // 已登录用户尝试访问登录或注册页面，重定向到首页
      next({ path: '/' })
    } else {
      next()
    }
  }
})

export default router