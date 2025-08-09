import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from 'axios'

// 抑制 ResizeObserver 错误（这是一个已知的浏览器兼容性问题，不影响功能）
const debounce = (fn, delay) => {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn.apply(null, args), delay)
  }
}

// 重写 ResizeObserver 以避免错误
const originalResizeObserver = window.ResizeObserver
window.ResizeObserver = class ResizeObserver extends originalResizeObserver {
  constructor(callback) {
    const wrappedCallback = debounce(callback, 20)
    super(wrappedCallback)
  }
}

// 全局错误处理
window.addEventListener('error', (e) => {
  if (e.message && e.message.includes('ResizeObserver loop completed with undelivered notifications')) {
    e.stopImmediatePropagation()
    return false
  }
})

// 处理未捕获的 Promise 错误
window.addEventListener('unhandledrejection', (e) => {
  if (e.reason && e.reason.message && e.reason.message.includes('ResizeObserver')) {
    e.preventDefault()
    return false
  }
})

// 配置axios默认URL
axios.defaults.baseURL = '/api'

// 创建Vue应用
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局挂载axios
app.config.globalProperties.$axios = axios

// 使用插件并挂载应用
app.use(router).use(ElementPlus).mount('#app')