<template>
  <div class="history-page">
    <el-card class="history-card">
      <!-- 页面头部 -->
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><DocumentIcon /></el-icon>
            <h2 class="header-title">历史识别记录</h2>
          </div>
          <div class="header-actions">
            <el-button 
              type="primary" 
              @click="showAiChat" 
              class="ai-chat-btn"
              :icon="ChatDotRound"
            >
              AI助手
            </el-button>
            <el-button 
              v-if="selectedRecords.length > 0"
              type="danger" 
              :icon="DeleteIcon" 
              @click="batchDelete"
              :loading="isBatchDeleting"
            >
              批量删除 ({{ selectedRecords.length }})
            </el-button>
            <el-button 
              type="primary" 
              :icon="RefreshIcon" 
              @click="refreshHistory"
              :loading="isLoading"
            >
              刷新
            </el-button>
            <el-button 
              type="success" 
              :icon="DownloadIcon" 
              @click="downloadHistory"
            >
              下载CSV
            </el-button>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-container">
        <el-icon class="loading-icon is-loading"><LoadingIcon /></el-icon>
        <p class="loading-text">正在加载历史记录...</p>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="records.length === 0" class="empty-container">
        <el-empty description="暂无历史记录">
          <el-button type="primary" @click="$router.push('/')">
            <el-icon><PlusIcon /></el-icon>
            开始识别
          </el-button>
        </el-empty>
      </div>
      
      <!-- 数据表格 -->
      <div v-else class="table-container">
        <el-table 
          :data="records" 
          stripe 
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column type="index" label="#" width="60" align="center" />
          <el-table-column prop="图片名" label="图片名" min-width="150">
            <template #default="scope">
              <el-text class="filename">{{ scope.row.图片名 }}</el-text>
            </template>
          </el-table-column>
          <el-table-column prop="车牌号" label="车牌号码" min-width="120">
            <template #default="scope">
              <el-tag type="primary" size="large">{{ scope.row.车牌号 }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="车牌颜色" label="车牌颜色" width="100">
            <template #default="scope">
              <el-tag :type="getColorType(scope.row.车牌颜色)">{{ scope.row.车牌颜色 }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="置信度" label="置信度" width="150">
            <template #default="scope">
              <div class="confidence-display">
                <el-progress 
                  :percentage="getConfidencePercentage(scope.row.置信度)" 
                  :color="getConfidenceColor(scope.row.置信度)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="confidence-text">{{ formatConfidence(scope.row.置信度) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="识别时间" label="识别时间" min-width="160">
            <template #default="scope">
              <el-text class="timestamp">{{ scope.row.识别时间 }}</el-text>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="scope">
              <el-button 
                type="danger" 
                size="small" 
                @click="deleteRecord(scope.$index)"
                :loading="isDeleting && deleteIndex === scope.$index"
              >
                <el-icon><DeleteIcon /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <!-- 确认删除对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="400px"
      align-center
    >
      <div class="delete-content">
        <el-icon class="warning-icon"><WarningFilledIcon /></el-icon>
        <p>确定要删除这条记录吗？此操作不可撤销。</p>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete" :loading="isDeleting">
          删除
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量删除确认对话框 -->
    <el-dialog
      v-model="batchDeleteDialogVisible"
      title="确认批量删除"
      width="450px"
      align-center
    >
      <div class="delete-content">
        <el-icon class="warning-icon"><WarningFilledIcon /></el-icon>
        <div>
          <p>确定要删除选中的 <strong>{{ selectedRecords.length }}</strong> 条记录吗？</p>
          <p class="warning-text">此操作不可撤销，请谨慎操作。</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="batchDeleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmBatchDelete" :loading="isBatchDeleting">
          批量删除
        </el-button>
      </template>
    </el-dialog>

    <!-- AI对话组件 -->
    <AiChat v-model="aiChatVisible" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { 
  Document as DocumentIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Loading as LoadingIcon,
  Plus as PlusIcon,
  Delete as DeleteIcon,
  WarningFilled as WarningFilledIcon,
  ChatDotRound
} from '@element-plus/icons-vue'
import AiChat from '@/components/AiChat.vue'

// 响应式数据
const records = ref([])
const isLoading = ref(true)
const deleteDialogVisible = ref(false)
const deleteIndex = ref(-1)
const isDeleting = ref(false)
const selectedRecords = ref([])
const isBatchDeleting = ref(false)
const batchDeleteDialogVisible = ref(false)
const aiChatVisible = ref(false)

// 方法定义
const fetchHistory = async () => {
  isLoading.value = true
  
  try {
    const response = await axios.get('/history')
    
    if (response.data.status === 'success') {
      records.value = response.data.records || []
    } else {
      ElMessage.error('获取历史记录失败')
    }
  } catch (error) {
    console.error('获取历史记录错误:', error)
    ElMessage.error('获取历史记录时发生错误')
  } finally {
    isLoading.value = false
  }
}

const refreshHistory = () => {
  fetchHistory()
}

const downloadHistory = () => {
  // 创建一个隐藏的a标签，用于下载文件
  const link = document.createElement('a')
  link.href = '/api/download_history'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('开始下载历史记录')
}

const deleteRecord = (index) => {
  deleteIndex.value = index
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  if (deleteIndex.value === -1) return
  
  isDeleting.value = true
  
  try {
    const response = await axios.post('/delete_history_record', {
      idx: deleteIndex.value
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('记录已删除')
      fetchHistory() // 重新加载数据
    } else {
      ElMessage.error(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除记录错误:', error)
    ElMessage.error('删除记录时发生错误')
  } finally {
    deleteDialogVisible.value = false
    deleteIndex.value = -1
    isDeleting.value = false
  }
}

// 获取颜色类型
const getColorType = (color) => {
  const colorMap = {
    '蓝': 'primary',
    '黄': 'warning',
    '白': 'info',
    '黑': '',
    '绿': 'success',
    '红': 'danger'
  }
  return colorMap[color] || 'info'
}

// 获取置信度百分比
const getConfidencePercentage = (confidence) => {
  if (!confidence && confidence !== 0) return 0
  
  if (typeof confidence === 'string') {
    // 处理百分比格式的字符串 (如 "85.5%")
    const percentMatch = confidence.match(/(\d+\.?\d*)%/)
    if (percentMatch) {
      return parseFloat(percentMatch[1])
    }
    // 处理小数格式的字符串 (如 "0.855")
    const floatValue = parseFloat(confidence)
    if (!isNaN(floatValue)) {
      return floatValue <= 1 ? Math.round(floatValue * 100) : floatValue
    }
    return 0
  }
  
  if (typeof confidence === 'number') {
    // 如果是小数 (0-1)，转换为百分比
    if (confidence <= 1) {
      return Math.round(confidence * 100)
    }
    // 如果已经是百分比 (>1)，直接返回
    return Math.round(confidence)
  }
  
  return 0
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  const percentage = getConfidencePercentage(confidence)
  if (percentage >= 90) return '#67c23a'
  if (percentage >= 70) return '#e6a23c'
  if (percentage >= 50) return '#f56c6c'
  return '#909399'
}

// 格式化置信度显示
const formatConfidence = (confidence) => {
  const percentage = getConfidencePercentage(confidence)
  return `${percentage}%`
}

// 处理表格选择变化
const handleSelectionChange = (selection) => {
  selectedRecords.value = selection
}

// 批量删除
const batchDelete = () => {
  if (selectedRecords.value.length === 0) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }
  batchDeleteDialogVisible.value = true
}

// 确认批量删除
const confirmBatchDelete = async () => {
  if (selectedRecords.value.length === 0) return
  
  isBatchDeleting.value = true
  
  try {
    // 获取选中记录的索引
    const indices = selectedRecords.value.map(record => {
      return records.value.findIndex(r => r === record)
    }).filter(index => index !== -1)
    
    const response = await axios.post('/batch_delete_history', {
      indices: indices
    })
    
    if (response.data.status === 'success') {
      ElMessage.success(`成功删除 ${indices.length} 条记录`)
      selectedRecords.value = []
      fetchHistory() // 重新加载数据
    } else {
      ElMessage.error(response.data.message || '批量删除失败')
    }
  } catch (error) {
    console.error('批量删除错误:', error)
    ElMessage.error('批量删除时发生错误')
  } finally {
    batchDeleteDialogVisible.value = false
    isBatchDeleting.value = false
  }
}

// 显示AI对话
const showAiChat = () => {
  aiChatVisible.value = true
}

// 生命周期
onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.history-card {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* 卡片头部样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
  color: #409EFF;
}

.header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.ai-chat-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
  transition: all 0.3s ease;
}

.ai-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
  background: linear-gradient(135deg, #ee5a24 0%, #ff6b6b 100%);
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #606266;
}

.loading-icon {
  font-size: 32px;
  color: #409EFF;
  margin-bottom: 16px;
}

.loading-text {
  font-size: 16px;
  margin: 0;
}

/* 空状态样式 */
.empty-container {
  padding: 40px 20px;
}

/* 表格容器样式 */
.table-container {
  margin-top: 20px;
}

/* 表格内容样式 */
.filename {
  font-weight: 500;
  color: #606266;
}

.timestamp {
  color: #909399;
  font-size: 14px;
}

/* 置信度显示样式 */
.confidence-display {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.confidence-display .el-progress {
  width: 80px;
}

.confidence-text {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  min-width: 40px;
}

/* 删除对话框样式 */
.delete-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
}

.warning-icon {
  font-size: 24px;
  color: #E6A23C;
  flex-shrink: 0;
}

.delete-content p {
  margin: 0;
  color: #606266;
  line-height: 1.5;
}

.warning-text {
  font-size: 13px;
  color: #909399;
  margin-top: 8px !important;
}

/* Element Plus 组件样式覆盖 */
:deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th) {
  font-weight: 600;
}

:deep(.el-table td) {
  padding: 12px 0;
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: #f5f7fa;
}

:deep(.el-button.is-circle) {
  width: 32px;
  height: 32px;
  padding: 0;
}

:deep(.el-progress-bar__outer) {
  border-radius: 4px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 4px;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}

:deep(.el-tag.el-tag--large) {
  padding: 6px 12px;
  font-size: 14px;
}

:deep(.el-empty) {
  padding: 40px 0;
}

:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 10px;
}

:deep(.el-dialog__body) {
  padding: 10px 24px 20px;
}

:deep(.el-dialog__footer) {
  padding: 10px 24px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .history-page {
    padding: 15px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .header-title {
    font-size: 18px;
  }
  
  :deep(.el-card__header) {
    padding: 16px 20px;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
  
  :deep(.el-table) {
    font-size: 14px;
  }
  
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 0 5%;
  }
}

@media (max-width: 480px) {
  .history-page {
    padding: 10px;
  }
  
  .header-left {
    gap: 8px;
  }
  
  .header-title {
    font-size: 16px;
  }
  
  .header-actions {
    gap: 8px;
  }
  
  :deep(.el-button) {
    padding: 8px 12px;
    font-size: 14px;
  }
  
  :deep(.el-card__header) {
    padding: 12px 16px;
  }
  
  :deep(.el-card__body) {
    padding: 16px;
  }
  
  :deep(.el-table td) {
    padding: 8px 0;
  }
  
  .delete-content {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
}
</style>