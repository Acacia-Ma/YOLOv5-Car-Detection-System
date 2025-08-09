<template>
  <div class="login-container">
    <div class="login-background">
      <div class="login-card">
        <div class="login-header">
          <div class="logo-section">
            <el-icon class="logo-icon" size="48">
              <Camera />
            </el-icon>
            <h1 class="system-title">车牌识别系统</h1>
            <p class="system-subtitle">智能车牌检测与识别平台</p>
          </div>
        </div>
        
        <el-card class="login-form-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon">
                <User />
              </el-icon>
              <span class="header-title">用户登录</span>
            </div>
          </template>
          
          <el-form 
            ref="loginForm" 
            :model="loginData" 
            :rules="rules" 
            @submit.prevent="login"
            size="large"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginData.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                clearable
                autocomplete="username"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="loginData.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                clearable
                autocomplete="current-password"
                @keyup.enter="login"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                class="login-button"
                :loading="isLoading"
                @click="login"
                size="large"
              >
                <el-icon v-if="!isLoading">
                  <Right />
                </el-icon>
                {{ isLoading ? '登录中...' : '登录' }}
              </el-button>
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="info" 
                class="register-button"
                plain
                @click="$router.push('/register')"
                size="large"
              >
                <el-icon>
                  <UserFilled />
                </el-icon>
                注册新账号
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <div class="login-footer">
          <p>© 2025 车牌识别系统 - 基于YOLOv5深度学习技术</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { User, Lock, Right, UserFilled, Camera } from '@element-plus/icons-vue'

// 响应式数据
const loginData = ref({
  username: '',
  password: ''
})
const isLoading = ref(false)
const loginForm = ref(null)

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 路由
const router = useRouter()
const route = useRoute()

// 方法
const login = async () => {
  // 验证表单
  try {
    await loginForm.value.validate()
  } catch (error) {
    return
  }
  
  isLoading.value = true
  
  try {
    const response = await axios.post('/login', {
      username: loginData.value.username,
      password: loginData.value.password
    })
    
    if (response.data.status === 'success') {
      // 保存用户信息到本地存储
      localStorage.setItem('username', response.data.username)
      
      // 保存完整的用户信息（包括角色）
      const userInfo = {
        id: response.data.id,
        username: response.data.username,
        role: response.data.role,
        is_active: response.data.is_active
      }
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
      
      // 显示成功消息
      ElMessage.success('登录成功！欢迎回来')
      
      // 重定向到首页或之前尝试访问的页面
      const redirectPath = route.query.redirect || '/'
      router.push(redirectPath)
    }
  } catch (error) {
    console.error('登录错误:', error)
    let errorMessage = '登录失败，请检查用户名和密码'
    
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage = error.response.data.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-background {
  width: 100%;
  max-width: 1200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-icon {
  color: #ffffff;
  margin-bottom: 15px;
  background: rgba(255, 255, 255, 0.1);
  padding: 15px;
  border-radius: 50%;
  backdrop-filter: blur(10px);
}

.system-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 10px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  background: linear-gradient(45deg, #ffffff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.system-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

.login-form-card {
  width: 100%;
  border-radius: 15px;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #409eff;
}

.header-icon {
  font-size: 1.5rem;
}

.login-button {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(45deg, #409eff, #67c23a);
  border: none;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
}

.register-button {
  width: 100%;
  height: 45px;
  font-size: 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.register-button:hover {
  transform: translateY(-1px);
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.login-footer p {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 10px;
  }
  
  .system-title {
    font-size: 2rem;
  }
  
  .system-subtitle {
    font-size: 1rem;
  }
  
  .login-card {
    max-width: 350px;
  }
}

/* Element Plus 组件样式覆盖 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-card__header) {
  padding: 20px;
  background: linear-gradient(45deg, #f8f9fa, #ffffff);
  border-bottom: 1px solid #e9ecef;
}

:deep(.el-card__body) {
  padding: 30px;
}
</style>