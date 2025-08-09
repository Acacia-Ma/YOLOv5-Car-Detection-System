<template>
  <div id="app">
    <!-- Element Plus 导航栏 -->
    <el-header class="app-header">
      <div class="header-content">
        <div class="brand">
          <el-icon class="brand-icon"><CarIcon /></el-icon>
          <router-link to="/" class="brand-text">车牌识别系统</router-link>
        </div>
        
        <el-menu
          mode="horizontal"
          :default-active="activeIndex"
          class="nav-menu"
          background-color="transparent"
          text-color="#ffffff"
          active-text-color="#409EFF"
        >
          <template v-if="!isLoggedIn">
            <el-menu-item index="login">
              <router-link to="/login" class="nav-link">
                <el-icon><UserIcon /></el-icon>
                <span>登录</span>
              </router-link>
            </el-menu-item>
            <el-menu-item index="register">
              <router-link to="/register" class="nav-link">
                <el-icon><EditPenIcon /></el-icon>
                <span>注册</span>
              </router-link>
            </el-menu-item>
          </template>
          <template v-else>
            <el-menu-item index="home">
              <router-link to="/" class="nav-link">
                <el-icon><HomeFilledIcon /></el-icon>
                <span>首页</span>
              </router-link>
            </el-menu-item>
            <el-menu-item index="history">
              <router-link to="/history" class="nav-link">
                <el-icon><DocumentIcon /></el-icon>
                <span>历史记录</span>
              </router-link>
            </el-menu-item>
            <el-menu-item v-if="userInfo && userInfo.role === 'admin'" index="admin">
              <router-link to="/admin" class="nav-link">
                <el-icon><SettingIcon /></el-icon>
                <span>管理员</span>
              </router-link>
            </el-menu-item>
            <el-sub-menu index="user">
              <template #title>
                <el-icon><UserIcon /></el-icon>
                <span>{{ username }}</span>
              </template>
              <el-menu-item index="logout" @click="logout">
                <el-icon><SwitchButtonIcon /></el-icon>
                <span>注销</span>
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </div>
    </el-header>

    <!-- 主要内容区域 -->
    <el-main class="app-main">
      <router-view @flash="setFlashMessage"></router-view>
    </el-main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  User as UserIcon,
  EditPen as EditPenIcon,
  HomeFilled as HomeFilledIcon,
  Document as DocumentIcon,
  SwitchButton as SwitchButtonIcon,
  Car as CarIcon,
  Setting as SettingIcon
} from '@element-plus/icons-vue'

// 响应式数据
const isLoggedIn = ref(false)
const username = ref('')
const userInfo = ref(null)
const activeIndex = ref('home')

// 路由
const router = useRouter()
const route = useRoute()

// 方法
const checkLoginStatus = () => {
  const storedUsername = localStorage.getItem('username')
  const storedUserInfo = localStorage.getItem('userInfo')
  if (storedUsername) {
    isLoggedIn.value = true
    username.value = storedUsername
    if (storedUserInfo) {
      userInfo.value = JSON.parse(storedUserInfo)
    }
  } else {
    isLoggedIn.value = false
    username.value = ''
    userInfo.value = null
  }
}

const logout = () => {
  localStorage.removeItem('username')
  localStorage.removeItem('userInfo')
  isLoggedIn.value = false
  username.value = ''
  userInfo.value = null
  ElMessage.success('已成功注销')
  router.push('/login')
}

const setFlashMessage = (message, type = 'success') => {
  // 使用 Element Plus 的消息提示
  if (type === 'success') {
    ElMessage.success(message)
  } else if (type === 'error') {
    ElMessage.error(message)
  } else if (type === 'warning') {
    ElMessage.warning(message)
  } else {
    ElMessage.info(message)
  }
}

const updateActiveIndex = (path) => {
  if (path === '/login') {
    activeIndex.value = 'login'
  } else if (path === '/register') {
    activeIndex.value = 'register'
  } else if (path === '/history') {
    activeIndex.value = 'history'
  } else if (path === '/admin') {
    activeIndex.value = 'admin'
  } else {
    activeIndex.value = 'home'
  }
}

// 生命周期
onMounted(() => {
  // 检查本地存储中是否有登录信息
  checkLoginStatus()

  // 监听路由变化，检查登录状态和更新活动菜单
  router.afterEach((to) => {
    checkLoginStatus()
    updateActiveIndex(to.path)
  })

  // 初始化活动菜单
  updateActiveIndex(route.path)
})

// 暴露给模板的方法
defineExpose({
  setFlashMessage
})
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 头部样式 */
.app-header {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  height: 60px !important;
  line-height: 60px;
  padding: 0 !important;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  font-size: 24px;
  color: #409EFF;
}

.brand-text {
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
  text-decoration: none;
  transition: color 0.3s ease;
}

.brand-text:hover {
  color: #409EFF;
}

/* 导航菜单样式 */
.nav-menu {
  border: none !important;
  background: transparent !important;
}

.nav-menu .el-menu-item {
  border: none !important;
  padding: 0 15px;
  margin: 0 5px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.nav-menu .el-menu-item:hover {
  background-color: rgba(64, 158, 255, 0.1) !important;
  color: #409EFF !important;
}

.nav-menu .el-menu-item.is-active {
  background-color: rgba(64, 158, 255, 0.2) !important;
  color: #409EFF !important;
}

.nav-menu .el-sub-menu {
  border: none !important;
}

.nav-menu .el-sub-menu .el-sub-menu__title {
  border: none !important;
  padding: 0 15px;
  margin: 0 5px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.nav-menu .el-sub-menu .el-sub-menu__title:hover {
  background-color: rgba(64, 158, 255, 0.1) !important;
  color: #409EFF !important;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: inherit;
  text-decoration: none;
  font-weight: 500;
}

.nav-link:hover {
  color: inherit;
  text-decoration: none;
}

/* 主要内容区域 */
.app-main {
  flex: 1;
  padding: 20px;
  background: transparent;
  overflow-y: auto;
}

/* Element Plus 组件样式覆盖 */
.el-header {
  padding: 0 !important;
}

.el-main {
  padding: 20px !important;
}

/* 下拉菜单样式 */
.el-popper {
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  z-index: 9999 !important;
}

.el-menu--popup {
  border-radius: 8px !important;
  background-color: #ffffff !important;
  border: 1px solid #e4e7ed !important;
  min-width: 120px !important;
}

.el-menu--popup .el-menu-item {
  border-radius: 6px !important;
  margin: 4px 8px !important;
  transition: all 0.3s ease !important;
  color: #606266 !important;
  font-size: 14px !important;
  line-height: 36px !important;
  height: 36px !important;
  padding: 0 12px !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

.el-menu--popup .el-menu-item:hover {
  background-color: #f5f7fa !important;
  color: #409EFF !important;
}

.el-menu--popup .el-menu-item .el-icon {
  font-size: 16px !important;
  margin-right: 0 !important;
}

/* 确保子菜单标题样式正确 */
.el-sub-menu__title {
  color: #ffffff !important;
}

.el-sub-menu__title:hover {
  color: #409EFF !important;
}

.el-sub-menu.is-active .el-sub-menu__title {
  color: #409EFF !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 15px;
  }
  
  .brand-text {
    font-size: 18px;
  }
  
  .nav-menu .el-menu-item,
  .nav-menu .el-sub-menu .el-sub-menu__title {
    padding: 0 10px;
    margin: 0 2px;
  }
  
  .nav-link span {
    display: none;
  }
  
  .app-main {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0 10px;
  }
  
  .brand {
    gap: 8px;
  }
  
  .brand-text {
    font-size: 16px;
  }
  
  .nav-menu .el-menu-item,
  .nav-menu .el-sub-menu .el-sub-menu__title {
    padding: 0 8px;
    margin: 0 1px;
  }
  
  .app-main {
    padding: 10px;
  }
}
</style>