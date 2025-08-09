<template>
  <div class="register-container">
    <div class="register-background">
      <div class="register-card">
        <div class="register-header">
          <div class="logo-section">
            <el-icon class="logo-icon" size="48">
              <UserFilled />
            </el-icon>
            <h1 class="system-title">用户注册</h1>
            <p class="system-subtitle">创建您的车牌识别系统账户</p>
          </div>
        </div>
        
        <el-card class="register-form-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon">
                <EditPen />
              </el-icon>
              <span class="header-title">注册新账号</span>
            </div>
          </template>
          
          <el-form 
            ref="registerForm" 
            :model="registerData" 
            :rules="rules" 
            @submit.prevent="register"
            size="large"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerData.username"
                placeholder="请输入用户名（3-20个字符）"
                :prefix-icon="User"
                clearable
                autocomplete="username"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="registerData.password"
                type="password"
                placeholder="请输入密码（6-20个字符）"
                :prefix-icon="Lock"
                show-password
                clearable
                autocomplete="new-password"
              />
            </el-form-item>
            
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerData.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="Lock"
                show-password
                clearable
                autocomplete="new-password"
                @keyup.enter="register"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                class="register-button"
                :loading="isLoading"
                @click="register"
                size="large"
              >
                <el-icon v-if="!isLoading">
                  <Check />
                </el-icon>
                {{ isLoading ? '注册中...' : '立即注册' }}
              </el-button>
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="info" 
                class="login-button"
                plain
                @click="$router.push('/login')"
                size="large"
              >
                <el-icon>
                  <Back />
                </el-icon>
                返回登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <div class="register-footer">
          <p>© 2025 车牌识别系统 - 基于YOLOv5深度学习技术</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { User, Lock, Check, Back, UserFilled, EditPen } from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const registerData = ref({
  username: '',
  password: '',
  confirmPassword: ''
})
const isLoading = ref(false)
const registerForm = ref(null)

// 自定义验证器
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerData.value.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const rules = ref({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
})

// 注册方法
const register = async () => {
  // 验证表单
  try {
    await registerForm.value.validate()
  } catch (error) {
    return
  }
  
  isLoading.value = true
  
  try {
    const response = await axios.post('/register', {
      username: registerData.value.username,
      password: registerData.value.password
    })
    
    if (response.data.status === 'success') {
      ElMessage.success(response.data.message || '注册成功！请登录')
      router.push('/login')
    }
  } catch (error) {
    console.error('注册错误:', error)
    let errorMessage = '注册失败，请重试'
    
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
.register-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.register-background {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-card {
  width: 100%;
  max-width: 450px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.register-header {
  text-align: center;
  padding: 40px 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: white;
}

.system-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: 1px;
}

.system-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

.register-form-card {
  margin: 0;
  border: none;
  box-shadow: none;
  background: transparent;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.header-icon {
  color: #667eea;
}

.header-title {
  color: #333;
}

.register-footer {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
}

/* Element Plus 组件样式覆盖 */
:deep(.el-card__header) {
  padding: 20px 40px 10px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 30px 40px 40px;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-input) {
  height: 48px;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e6ed;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

:deep(.el-input__inner) {
  height: 46px;
  line-height: 46px;
  font-size: 16px;
  color: #333;
}

:deep(.el-input__prefix) {
  left: 16px;
  color: #667eea;
}

:deep(.el-input__suffix) {
  right: 16px;
}

.register-button,
.login-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
  margin-bottom: 12px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

:deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

:deep(.el-button--info) {
  background: #f8f9fa;
  border: 1px solid #e0e6ed;
  color: #666;
}

:deep(.el-button--info:hover) {
  background: #e9ecef;
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
}

:deep(.el-form-item__error) {
  color: #f56565;
  font-size: 13px;
  margin-top: 6px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-container {
    padding: 10px;
  }
  
  .register-header {
    padding: 30px 20px 15px;
  }
  
  .system-title {
    font-size: 24px;
  }
  
  .system-subtitle {
    font-size: 14px;
  }
  
  :deep(.el-card__header) {
    padding: 15px 20px 10px;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

/* 加载动画 */
:deep(.el-button.is-loading) {
  position: relative;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>