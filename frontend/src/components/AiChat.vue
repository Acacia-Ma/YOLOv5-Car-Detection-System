<template>
  <el-dialog
    v-model="visible"
    title="AI智能助手 - 车牌识别专家"
    width="800px"
    :before-close="handleClose"
    :show-close="false"
    class="ai-chat-dialog"
  >
    <template #header="{ close, titleId, titleClass }">
      <div class="dialog-header">
        <div class="header-left">
          <span :id="titleId" :class="titleClass">AI智能助手 - 车牌识别专家</span>
        </div>
        <div class="header-right">
          <el-button
            type="primary"
            size="small"
            @click="showConfig"
            class="config-btn"
          >
            <el-icon><Setting /></el-icon>
            配置
          </el-button>
          <el-button
            type="info"
            size="small"
            circle
            @click="close"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </template>
    <div class="chat-container">
      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="welcome-content">
            <el-icon class="welcome-icon"><Robot /></el-icon>
            <h3>欢迎使用AI智能助手！</h3>
            <p>我是专门为车牌识别系统设计的AI助手，可以帮助您：</p>
            <ul>
              <li>🚗 解答车牌识别相关问题</li>
              <li>📸 分析上传的车牌图片</li>
              <li>🔧 提供系统使用指导</li>
              <li>📊 解释识别结果和置信度</li>
              <li>❓ 解决使用过程中的问题</li>
            </ul>
            <div class="config-notice">
              <el-alert
                title="💡 提示"
                type="info"
                :closable="false"
                show-icon
              >
                <template #default>
                  <p>为了获得更智能的AI回复，请先点击右上角的"配置"按钮设置您的GitHub PAT token。</p>
                  <p>如果未配置，系统将使用基础的规则回复功能。</p>
                </template>
              </el-alert>
            </div>
            <p>请输入您的问题或上传图片开始对话！</p>
          </div>
        </div>
        
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.type]"
        >
          <div class="message-avatar">
            <el-avatar v-if="message.type === 'user'" :icon="UserFilled" />
            <el-avatar v-else class="ai-avatar">
              <el-icon><Robot /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <!-- 文本消息 -->
              <div v-if="message.content" class="text-content" v-html="formatMessage(message.content)"></div>
              
              <!-- 图片消息 -->
              <div v-if="message.image" class="image-content">
                <img :src="message.image" alt="上传的图片" class="chat-image" @click="previewImage(message.image)" />
              </div>
              
              <!-- 加载状态 -->
              <div v-if="message.loading" class="loading-content">
                <el-icon class="loading-icon is-loading"><Loading /></el-icon>
                <span>AI正在思考中...</span>
              </div>
            </div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="chat-input">
        <!-- 图片上传预览 -->
        <div v-if="uploadPreview" class="upload-preview">
          <div class="preview-container">
            <img :src="uploadPreview" alt="预览图片" class="preview-image" />
            <el-button
              type="danger"
              size="small"
              circle
              @click="clearUpload"
              class="remove-btn"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
        
        <!-- 输入框和按钮 -->
        <div class="input-row">
          <el-upload
            :show-file-list="false"
            :before-upload="beforeUpload"
            :on-change="handleImageUpload"
            :auto-upload="false"
            accept="image/*"
            class="image-upload"
          >
            <el-button type="primary" :icon="Picture" circle />
          </el-upload>
          
          <el-input
            v-model="inputMessage"
            placeholder="请输入您的问题..."
            type="textarea"
            :rows="2"
            @keydown.enter.exact="sendMessage"
            @keydown.ctrl.enter.exact="addNewLine"
            class="message-input"
          />
          
          <el-button
            type="primary"
            :loading="isLoading"
            @click="sendMessage"
            :disabled="!inputMessage.trim() && !uploadPreview"
            class="send-btn"
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imagePreviewVisible"
      title="图片预览"
      width="60%"
      append-to-body
    >
      <img :src="previewImageUrl" alt="预览图片" class="preview-dialog-image" />
    </el-dialog>

    <!-- AI配置对话框 -->
    <AiConfig v-model="configVisible" @config-saved="onConfigSaved" />
  </el-dialog>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import {
  Robot,
  UserFilled,
  Picture,
  Promotion,
  Close,
  Loading,
  Setting
} from '@element-plus/icons-vue'
import AiConfig from './AiConfig.vue'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

// 响应式数据
const visible = ref(props.modelValue)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const uploadPreview = ref('')
const uploadFile = ref(null)
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')
const configVisible = ref(false)

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// 监听visible变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 方法
const handleClose = () => {
  visible.value = false
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatMessage = (content) => {
  // 简单的markdown格式化
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }
  return false // 阻止自动上传
}

const handleImageUpload = (file) => {
  uploadFile.value = file.raw || file
  uploadPreview.value = URL.createObjectURL(uploadFile.value)
}

const clearUpload = () => {
  uploadPreview.value = ''
  uploadFile.value = null
}

const previewImage = (imageUrl) => {
  previewImageUrl.value = imageUrl
  imagePreviewVisible.value = true
}

const addNewLine = () => {
  inputMessage.value += '\n'
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() && !uploadPreview.value) {
    return
  }

  const userMessage = {
    type: 'user',
    content: inputMessage.value.trim(),
    image: uploadPreview.value,
    timestamp: Date.now()
  }

  messages.value.push(userMessage)
  
  // 添加AI加载消息
  const loadingMessage = {
    type: 'ai',
    loading: true,
    timestamp: Date.now()
  }
  messages.value.push(loadingMessage)
  
  scrollToBottom()

  const messageText = inputMessage.value.trim()
  const imageFile = uploadFile.value
  
  // 清空输入
  inputMessage.value = ''
  clearUpload()
  isLoading.value = true

  try {
    const formData = new FormData()
    formData.append('message', messageText)
    if (imageFile) {
      formData.append('image', imageFile)
    }

    const response = await axios.post('ai_chat', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // 移除加载消息
    messages.value.pop()

    if (response.data.status === 'success') {
      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        timestamp: Date.now()
      }
      messages.value.push(aiMessage)
    } else {
      const errorMessage = {
        type: 'ai',
        content: '抱歉，我现在无法回答您的问题。请稍后再试。',
        timestamp: Date.now()
      }
      messages.value.push(errorMessage)
    }
  } catch (error) {
    // 移除加载消息
    messages.value.pop()
    
    console.error('AI对话错误:', error)
    const errorMessage = {
      type: 'ai',
      content: '抱歉，连接AI服务时出现错误。请检查网络连接后重试。',
      timestamp: Date.now()
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 显示配置对话框
const showConfig = () => {
  configVisible.value = true
}

// 配置保存成功回调
const onConfigSaved = () => {
  ElMessage.success('AI配置已更新，现在可以使用GitHub模型进行对话了！')
}

// 清空对话历史
const clearHistory = () => {
  messages.value = []
}

// 暴露方法给父组件
defineExpose({
  clearHistory
})
</script>

<style scoped>
.ai-chat-dialog {
  border-radius: 16px;
}

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  margin: 0;
}

:deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.config-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 12px;
}

.config-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

:deep(.el-dialog__body) {
  padding: 0;
}

.chat-container {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
}

.welcome-content {
  max-width: 500px;
  margin: 0 auto;
}

.welcome-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.welcome-content h3 {
  color: #333;
  margin-bottom: 16px;
  font-size: 24px;
}

.welcome-content p {
  color: #666;
  margin-bottom: 16px;
  line-height: 1.6;
}

.welcome-content ul {
  text-align: left;
}

.config-notice {
  margin: 16px 0;
  text-align: left;
}

.config-notice p {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

.welcome-content li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  word-wrap: break-word;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.ai .message-bubble {
  background: white;
  border: 1px solid #e0e0e0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.text-content {
  line-height: 1.5;
}

.image-content {
  margin-top: 8px;
}

.chat-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.chat-image:hover {
  transform: scale(1.05);
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.loading-icon {
  font-size: 16px;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.message.user .message-time {
  text-align: right;
}

.chat-input {
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 16px 20px;
}

.upload-preview {
  margin-bottom: 12px;
}

.preview-container {
  position: relative;
  display: inline-block;
}

.preview-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  min-height: 20px;
}

.input-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.image-upload {
  flex-shrink: 0;
}

.message-input {
  flex: 1;
}

:deep(.message-input .el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #dcdfe6;
  resize: none;
}

.send-btn {
  flex-shrink: 0;
  height: 40px;
  border-radius: 12px;
}

.preview-dialog-image {
  width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 2.5%;
  }
  
  .chat-container {
    height: 500px;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .welcome-content {
    padding: 20px 10px;
  }
  
  .welcome-icon {
    font-size: 36px;
  }
  
  .welcome-content h3 {
    font-size: 20px;
  }
}
</style>