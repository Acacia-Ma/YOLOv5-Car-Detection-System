<template>
  <div class="home-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-title">
            <el-icon class="header-icon"><Camera /></el-icon>
            <h1>智能车牌识别系统</h1>
          </div>
          <p class="header-subtitle">基于YOLOv5的高精度车牌检测与识别</p>
        </div>
        <div class="header-right">
          <el-button 
            type="primary" 
            size="large"
            @click="showAiChat"
            class="ai-chat-btn"
          >
            <el-icon><ChatDotRound /></el-icon>
            AI助手
          </el-button>
        </div>
      </div>
    </div>

    <!-- 功能卡片区域 -->
    <div class="function-cards">
      <!-- 图片检测卡片 -->
      <el-card class="detection-card image-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon class="card-icon"><Picture /></el-icon>
            <span class="card-title">图片检测</span>
          </div>
        </template>
        
        <div class="card-content">
          <el-row :gutter="24">
            <!-- 图片上传区域 -->
            <el-col :span="12">
              <div class="upload-section">
                <el-upload
                  class="image-uploader"
                  :show-file-list="false"
                  :before-upload="beforeImageUpload"
                  :on-change="previewImage"
                  :auto-upload="false"
                  accept="image/*"
                  drag
                >
                  <div v-if="!previewUrl" class="upload-placeholder">
                    <el-icon class="upload-icon"><Plus /></el-icon>
                    <div class="upload-text">点击或拖拽上传图片</div>
                    <div class="upload-hint">支持 JPG、PNG 格式</div>
                  </div>
                  <img v-else :src="previewUrl" class="uploaded-image" @click="showFullImage" />
                </el-upload>
                
                <div class="upload-actions">
                  <el-button 
                    type="primary" 
                    size="large"
                    :loading="isLoading"
                    :disabled="!imageSelected"
                    @click="detectImage"
                    class="detect-btn"
                  >
                    <el-icon><Search /></el-icon>
                    {{ isLoading ? '识别中...' : '开始识别' }}
                  </el-button>
                </div>
              </div>
            </el-col>
            
            <!-- 识别结果区域 -->
            <el-col :span="12">
              <div class="result-section">
                <div v-if="resultUrl" class="result-container">
                  <div class="result-image-wrapper">
                    <img :src="resultUrl" class="result-image" @click="showFullImage" />
                    <div class="image-overlay">
                      <el-icon class="zoom-icon"><ZoomIn /></el-icon>
                    </div>
                  </div>
                  
                  <div v-if="plateInfo" class="plate-info">
                    <el-descriptions :column="1" border>
                      <el-descriptions-item label="车牌号码">
                        <el-tag type="primary" size="large">{{ plateInfo.plate_no || '未检测到' }}</el-tag>
                      </el-descriptions-item>
                      <el-descriptions-item label="车牌颜色">
                        <el-tag :type="getColorType(plateInfo.plate_color)">{{ plateInfo.plate_color || '未检测到' }}</el-tag>
                      </el-descriptions-item>
                      <el-descriptions-item label="置信度">
                        <div class="confidence-display">
                          <el-progress 
                            :percentage="getConfidencePercentage(plateInfo.confidence)" 
                            :color="getConfidenceColor(plateInfo.confidence)"
                            :show-text="false"
                            :stroke-width="20"
                          />
                          <span class="confidence-text">{{ formatConfidence(plateInfo.confidence) }}</span>
                        </div>
                      </el-descriptions-item>
                    </el-descriptions>
                  </div>
                </div>
                <div v-else class="empty-result">
                  <el-empty description="暂无识别结果" />
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 视频检测卡片 -->
      <el-card class="detection-card video-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon class="card-icon"><VideoPlay /></el-icon>
            <span class="card-title">视频检测</span>
          </div>
        </template>
        
        <div class="card-content">
          <!-- 视频上传区域 -->
          <div class="video-upload-section">
            <el-upload
              class="video-uploader"
              :show-file-list="false"
              :before-upload="beforeVideoUpload"
              :on-change="previewVideo"
              :auto-upload="false"
              accept="video/*"
              drag
            >
              <div v-if="!videoSelected" class="upload-placeholder">
                <el-icon class="upload-icon"><VideoPlay /></el-icon>
                <div class="upload-text">点击或拖拽上传视频</div>
                <div class="upload-hint">支持 MP4、AVI 格式</div>
              </div>
              <div v-else class="video-info">
                <el-icon class="video-icon"><VideoPlay /></el-icon>
                <span>{{ videoFile.name }}</span>
              </div>
            </el-upload>
            
            <div class="video-actions">
              <el-button 
                type="success" 
                size="large"
                :loading="isVideoUploading"
                :disabled="!videoSelected"
                @click="uploadVideo"
              >
                <el-icon><Upload /></el-icon>
                {{ isVideoUploading ? '上传中...' : '上传视频' }}
              </el-button>
              <el-button 
                type="primary" 
                size="large"
                :loading="isVideoDetecting"
                :disabled="!videoUploaded"
                @click="detectVideo"
              >
                <el-icon><Search /></el-icon>
                {{ isVideoDetecting ? '检测中...' : '开始检测' }}
              </el-button>
            </div>
          </div>
          
          <!-- 视频预览和结果 -->
          <el-row :gutter="24" v-if="videoPreviewUrl || videoResultUrl">
            <el-col :span="12" v-if="videoPreviewUrl">
              <div class="video-preview">
                <h4>原始视频</h4>
                <video :src="videoPreviewUrl" controls class="video-player"></video>
              </div>
            </el-col>
            <el-col :span="12" v-if="videoResultUrl">
              <div class="video-result">
                <h4>检测结果</h4>
                <video :src="videoResultUrl" controls class="video-player"></video>
              </div>
            </el-col>
          </el-row>
          
          <!-- 检测结果统计 -->
          <div v-if="videoDetectionResults.length > 0" class="detection-results">
            <h4>检测统计</h4>
            <el-table :data="videoDetectionResults" stripe style="width: 100%">
              <el-table-column prop="timestamp" label="时间点" width="120">
                <template #default="scope">
                  {{ scope.row.timestamp.toFixed(2) }}s
                </template>
              </el-table-column>
              <el-table-column prop="plate_no" label="车牌号码" />
              <el-table-column prop="plate_color" label="颜色">
                <template #default="scope">
                  <el-tag :type="getColorType(scope.row.plate_color)">{{ scope.row.plate_color }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="confidence" label="置信度" width="150">
                <template #default="scope">
                  <div class="confidence-display">
                    <el-progress 
                      :percentage="getConfidencePercentage(scope.row.confidence)" 
                      :color="getConfidenceColor(scope.row.confidence)"
                      :show-text="false"
                      :stroke-width="8"
                    />
                    <span class="confidence-text">{{ formatConfidence(scope.row.confidence) }}</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-card>

      <!-- 摄像头检测卡片 -->
      <el-card class="detection-card camera-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon class="card-icon"><Camera /></el-icon>
            <span class="card-title">摄像头实时检测</span>
          </div>
        </template>
        
        <div class="card-content">
          <div class="camera-controls">
            <el-button 
              type="warning" 
              size="large"
              :disabled="cameraActive"
              @click="startCamera"
              class="camera-btn"
            >
              <el-icon><VideoCamera /></el-icon>
              开启摄像头
            </el-button>
            <el-button 
              type="info" 
              size="large"
              :disabled="!cameraActive"
              @click="stopCamera"
              class="camera-btn"
            >
              <el-icon><VideoCameraFilled /></el-icon>
              关闭摄像头
            </el-button>
          </div>
          
          <!-- 摄像头画面 -->
          <div v-if="cameraActive" class="camera-feed">
            <img 
              :src="cameraFeedUrl" 
              class="camera-image" 
              alt="摄像头画面" 
              @error="handleCameraError"
            />
          </div>
          <div v-else class="camera-placeholder">
            <el-empty description="摄像头未开启" />
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imageDialogVisible"
      title="图片预览"
      width="80%"
      center
    >
      <div class="image-dialog-content">
        <img :src="modalImageUrl" class="dialog-image" />
      </div>
    </el-dialog>
    
    <!-- AI对话组件 -->
    <AiChat v-model="aiChatVisible" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import AiChat from '@/components/AiChat.vue'
import { 
  Camera, 
  Picture, 
  VideoPlay, 
  Plus, 
  Search, 
  ZoomIn, 
  Upload, 
  VideoCamera, 
  VideoCameraFilled,
  ChatDotRound
} from '@element-plus/icons-vue'

// 响应式数据
// 图片检测相关
const imageFile = ref(null)
const previewUrl = ref('')
const resultUrl = ref('')
const modalImageUrl = ref('')
const imageSelected = ref(false)
const isLoading = ref(false)
const plateInfo = ref(null)
const imageDialogVisible = ref(false)

// 视频检测相关
const videoFile = ref(null)
const videoSelected = ref(false)
const videoUploaded = ref(false)
const isVideoUploading = ref(false)
const isVideoDetecting = ref(false)
const videoPreviewUrl = ref('')
const videoResultUrl = ref('')
const videoDetectionResults = ref([])

// 摄像头相关
const cameraActive = ref(false)
const cameraFeedUrl = ref('')

// AI对话相关
const aiChatVisible = ref(false)
// 方法定义
// 图片上传前的处理
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB!')
    return false
  }
  return false // 阻止自动上传
}

const previewImage = (file) => {
  if (!file) {
    imageSelected.value = false
    previewUrl.value = ''
    return
  }
  
  imageFile.value = file.raw || file
  imageSelected.value = true
  previewUrl.value = URL.createObjectURL(imageFile.value)
  resultUrl.value = ''
  plateInfo.value = null
}

const detectImage = async () => {
  if (!imageFile.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  
  isLoading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', imageFile.value)
    
    const response = await axios.post('/detect_image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success') {
      // 添加时间戳防止缓存
      resultUrl.value = `/api${response.data.image_url}?t=${new Date().getTime()}`
      plateInfo.value = {
        plate_no: response.data.plate_no || '未检测到',
        plate_color: response.data.plate_color || '未检测到',
        confidence: response.data.confidence || '未检测到'
      }
      ElMessage.success('图片识别成功')
    } else {
      ElMessage.error(response.data.message || '识别失败')
    }
  } catch (error) {
    console.error('识别错误:', error)
    ElMessage.error('识别过程中发生错误')
  } finally {
    isLoading.value = false
  }
}

const showFullImage = (event) => {
  modalImageUrl.value = event.target.src
  imageDialogVisible.value = true
}

// 视频上传前的处理
const beforeVideoUpload = (file) => {
  const isVideo = file.type.startsWith('video/')
  const isLt100M = file.size / 1024 / 1024 < 100

  if (!isVideo) {
    ElMessage.error('只能上传视频文件!')
    return false
  }
  if (!isLt100M) {
    ElMessage.error('视频大小不能超过 100MB!')
    return false
  }
  return false // 阻止自动上传
}

// 视频相关方法
const previewVideo = (file) => {
  if (!file) {
    videoSelected.value = false
    videoPreviewUrl.value = ''
    return
  }
  
  videoFile.value = file.raw || file
  videoSelected.value = true
  videoPreviewUrl.value = URL.createObjectURL(videoFile.value)
  videoUploaded.value = false
  videoResultUrl.value = ''
  videoDetectionResults.value = []
}

const uploadVideo = async () => {
  if (!videoFile.value) {
    ElMessage.warning('请先选择视频')
    return
  }
  
  isVideoUploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('video', videoFile.value)
    
    const response = await axios.post('/upload_video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success') {
      videoUploaded.value = true
      ElMessage.success('视频上传成功，可以开始检测')
    } else {
      ElMessage.error(response.data.message || '视频上传失败')
    }
  } catch (error) {
    console.error('视频上传错误:', error)
    ElMessage.error('视频上传过程中发生错误')
  } finally {
    isVideoUploading.value = false
  }
}

const detectVideo = async () => {
  if (!videoUploaded.value) {
    ElMessage.warning('请先上传视频')
    return
  }
  
  isVideoDetecting.value = true
  ElMessage.info('视频检测中，请稍候...')
  
  try {
    const response = await axios.post('/detect_video')
    
    if (response.data.status === 'success') {
      videoResultUrl.value = `/api/${response.data.output_video}?t=${new Date().getTime()}`
      videoDetectionResults.value = response.data.detected_plates || []
      ElMessage.success('视频检测完成')
    } else {
      ElMessage.error(response.data.message || '视频检测失败')
    }
  } catch (error) {
    console.error('视频检测错误:', error)
    ElMessage.error('视频检测过程中发生错误')
  } finally {
    isVideoDetecting.value = false
  }
}

// 摄像头相关方法
const startCamera = () => {
  cameraActive.value = true
  cameraFeedUrl.value = `/api/camera_feed?t=${new Date().getTime()}`
  ElMessage.success('摄像头已开启')
}

const stopCamera = () => {
  cameraActive.value = false
  cameraFeedUrl.value = ''
  // 调用后端停止摄像头API
  axios.post('/stop_camera').catch(error => {
    console.error('停止摄像头错误:', error)
  })
  ElMessage.info('摄像头已关闭')
}

const handleCameraError = () => {
  ElMessage.error('摄像头连接失败，请检查摄像头是否可用')
  cameraActive.value = false
  cameraFeedUrl.value = ''
}

// 辅助方法
const getColorType = (color) => {
  const colorMap = {
    '蓝': 'primary',
    '黄': 'warning',
    '绿': 'success',
    '白': 'info',
    '黑': 'info'
  }
  return colorMap[color] || 'info'
}

const getConfidencePercentage = (confidence) => {
  if (confidence === null || confidence === undefined || confidence === '' || confidence === '未检测到') {
    return 0
  }
  const num = typeof confidence === 'string' ? parseFloat(confidence) : confidence
  if (isNaN(num)) return 0
  return Math.round(num * 100)
}

const getConfidenceColor = (confidence) => {
  if (confidence === null || confidence === undefined || confidence === '' || confidence === '未检测到') {
    return '#909399'
  }
  const num = typeof confidence === 'string' ? parseFloat(confidence) : confidence
  if (isNaN(num)) return '#909399'
  const percentage = num * 100
  if (percentage >= 80) return '#67c23a'
  if (percentage >= 60) return '#e6a23c'
  return '#f56c6c'
}

const formatConfidence = (confidence) => {
  if (confidence === null || confidence === undefined || confidence === '' || confidence === '未检测到') {
    return '未检测到'
  }
  const num = typeof confidence === 'string' ? parseFloat(confidence) : confidence
  if (isNaN(num)) return '未检测到'
  return `${(num * 100).toFixed(2)}%`
}

// AI对话相关方法
const showAiChat = () => {
  aiChatVisible.value = true
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

/* 页面头部 */
.page-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  color: white;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  flex: 1;
}

.header-right {
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.header-icon {
  font-size: 48px;
  color: white;
}

.header-title h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
}

.header-subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

/* AI对话按钮 */
.ai-chat-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 25px;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
  transition: all 0.3s ease;
}

.ai-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
  background: linear-gradient(135deg, #ff5252 0%, #d63031 100%);
}

/* 功能卡片区域 */
.function-cards {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.detection-card {
  border-radius: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.detection-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
}

.card-icon {
  font-size: 24px;
}

.image-card .card-header {
  color: #667eea;
}

.video-card .card-header {
  color: #48bb78;
}

.camera-card .card-header {
  color: #ed8936;
}

.card-title {
  font-size: 20px;
  font-weight: 600;
}

/* 卡片内容 */
.card-content {
  padding: 20px;
}

/* 上传区域 */
.upload-section, .video-upload-section {
  margin-bottom: 20px;
}

.image-uploader, .video-uploader {
  width: 100%;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border-radius: 16px;
  border: 2px dashed #d9d9d9;
  background: #fafafa;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

:deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: #f0f2ff;
}

.upload-placeholder {
  text-align: center;
  color: #666;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.upload-hint {
  font-size: 14px;
  color: #999;
}

.uploaded-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.uploaded-image:hover {
  transform: scale(1.02);
}

.video-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #333;
  font-size: 16px;
}

.video-icon {
  font-size: 32px;
  color: #48bb78;
}

/* 按钮区域 */
.upload-actions, .video-actions, .camera-controls {
  display: flex;
  gap: 16px;
  margin-top: 20px;
  justify-content: center;
}

.detect-btn, .camera-btn {
  min-width: 140px;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
}

/* 结果区域 */
.result-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.result-container {
  flex: 1;
}

.result-image-wrapper {
  position: relative;
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.result-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  cursor: pointer;
  transition: all 0.3s ease;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
}

.result-image-wrapper:hover .image-overlay {
  opacity: 1;
}

.zoom-icon {
  font-size: 32px;
  color: white;
}

.plate-info {
  margin-top: 16px;
}

:deep(.el-descriptions) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-descriptions__header) {
  background: #f8f9fa;
}

.empty-result {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 视频播放器 */
.video-preview, .video-result {
  margin-bottom: 20px;
}

.video-preview h4, .video-result h4 {
  margin-bottom: 12px;
  color: #333;
  font-weight: 600;
}

.video-player {
  width: 100%;
  height: 250px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* 检测结果表格 */
.detection-results {
  margin-top: 30px;
}

.detection-results h4 {
  margin-bottom: 16px;
  color: #333;
  font-weight: 600;
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

:deep(.el-table th) {
  background: #f8f9fa;
  color: #333;
  font-weight: 600;
}

/* 置信度显示样式 */
.confidence-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence-display .el-progress {
  flex: 1;
  min-width: 120px;
}

.confidence-display .confidence-text {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  min-width: 80px;
  text-align: right;
}

.confidence-text {
  margin-left: 8px;
  font-size: 12px;
  color: #666;
}

/* 摄像头区域 */
.camera-feed {
  text-align: center;
  margin-top: 20px;
}

.camera-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.camera-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 图片预览对话框 */
.image-dialog-content {
  text-align: center;
}

.dialog-image {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Element Plus 组件样式覆盖 */
:deep(.el-card__header) {
  padding: 20px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

:deep(.el-card__body) {
  padding: 0;
}

:deep(.el-button) {
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-2px);
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

:deep(.el-button--success) {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
}

:deep(.el-button--warning) {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(237, 137, 54, 0.4);
}

:deep(.el-button--info) {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(160, 174, 192, 0.4);
}

:deep(.el-progress-bar__outer) {
  border-radius: 10px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
}

:deep(.el-tag) {
  border-radius: 8px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home-container {
    padding: 10px;
  }
  
  .page-header {
    padding: 30px 15px;
    margin-bottom: 20px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .header-left {
    flex: none;
  }
  
  .header-title {
    justify-content: center;
  }
  
  .header-title h1 {
    font-size: 28px;
  }
  
  .header-subtitle {
    font-size: 16px;
  }
  
  .ai-chat-btn {
    padding: 10px 20px;
    font-size: 14px;
  }
  
  .function-cards {
    gap: 20px;
  }
  
  .card-content {
    padding: 15px;
  }
  
  .upload-actions, .video-actions, .camera-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .detect-btn, .camera-btn {
    width: 100%;
    max-width: 300px;
  }
  
  :deep(.el-col) {
    margin-bottom: 20px;
  }
}

@media (max-width: 480px) {
  .header-title {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-icon {
    font-size: 36px;
  }
  
  .header-title h1 {
    font-size: 24px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
  
  :deep(.el-upload-dragger) {
    height: 150px;
  }
}
</style>