<template>
  <div class="admin-container">
    <!-- 页面头部 -->
    <div class="admin-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-title">
            <el-icon class="header-icon"><Setting /></el-icon>
            <h1>管理员控制台</h1>
          </div>
        </div>
        <div class="header-right">
          <el-button 
            type="primary" 
            @click="showAiChat" 
            class="ai-chat-btn"
            :icon="ChatDotRound"
          >
            AI助手
          </el-button>
          <div class="header-info">
            <el-avatar :size="40" class="user-avatar">
              {{ currentUser.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <div class="user-info">
              <p class="welcome-text">欢迎回来</p>
              <p class="username">{{ currentUser.username }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="card" class="admin-tabs">
      <!-- 系统统计 -->
      <el-tab-pane label="系统统计" name="statistics">
        <div class="statistics-section">
          <el-row :gutter="24">
            <el-col :span="8">
              <el-card class="stat-card users-card" shadow="hover">
                <div class="stat-item">
                  <div class="stat-icon">
                    <el-icon><User /></el-icon>
                  </div>
                  <div class="stat-content">
                    <h3>用户统计</h3>
                    <div class="stat-numbers">
                      <div class="stat-number">
                        <span class="number">{{ statistics.users.total }}</span>
                        <span class="label">总用户数</span>
                      </div>
                      <div class="stat-number">
                        <span class="number">{{ statistics.users.active }}</span>
                        <span class="label">活跃用户</span>
                      </div>
                      <div class="stat-number">
                        <span class="number">{{ statistics.users.admin }}</span>
                        <span class="label">管理员</span>
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="stat-card detection-card" shadow="hover">
                <div class="stat-item">
                  <div class="stat-icon">
                    <el-icon><DataAnalysis /></el-icon>
                  </div>
                  <div class="stat-content">
                    <h3>今日识别</h3>
                    <div class="stat-numbers">
                      <div class="stat-number">
                        <span class="number">{{ statistics.detections.today }}</span>
                        <span class="label">总识别次数</span>
                      </div>
                      <div class="stat-number">
                        <span class="number">{{ statistics.detections.today_successful }}</span>
                        <span class="label">成功识别</span>
                      </div>
                      <div class="stat-number">
                        <span class="number">{{ getSuccessRate() }}%</span>
                        <span class="label">成功率</span>
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="stat-card history-card" shadow="hover">
                <div class="stat-item">
                  <div class="stat-icon">
                    <el-icon><TrendCharts /></el-icon>
                  </div>
                  <div class="stat-content">
                    <h3>历史统计</h3>
                    <div class="stat-numbers">
                      <div class="stat-number">
                        <span class="number">{{ statistics.detections.all_time }}</span>
                        <span class="label">总识别次数</span>
                      </div>
                    </div>
                    <el-button type="primary" @click="refreshStatistics" class="refresh-btn">
                      <el-icon><Refresh /></el-icon>
                      刷新统计
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="management-section">
          <el-card class="management-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon class="section-icon"><User /></el-icon>
                  <span class="section-title">用户管理</span>
                </div>
                <div class="header-actions">
                  <el-button type="primary" @click="refreshUsers" :loading="usersLoading">
                    <el-icon><Refresh /></el-icon>
                    刷新列表
                  </el-button>
                </div>
              </div>
            </template>
            
            <el-table :data="users" style="width: 100%" v-loading="usersLoading" class="modern-table">
              <el-table-column prop="id" label="ID" width="80" align="center"></el-table-column>
              <el-table-column prop="username" label="用户名" width="150">
                <template #default="scope">
                  <div class="user-info">
                    <el-avatar :size="32" class="user-avatar-small">
                      {{ scope.row.username.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <span class="username">{{ scope.row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="role" label="角色" width="120" align="center">
                <template #default="scope">
                  <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'primary'" effect="dark">
                    <el-icon><Crown v-if="scope.row.role === 'admin'" /><User v-else /></el-icon>
                    {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="注册时间" width="180" align="center"></el-table-column>
              <el-table-column prop="is_active" label="状态" width="100" align="center">
                <template #default="scope">
                  <el-tag :type="scope.row.is_active ? 'success' : 'danger'" effect="dark">
                    <el-icon><CircleCheck v-if="scope.row.is_active" /><CircleClose v-else /></el-icon>
                    {{ scope.row.is_active ? '活跃' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" align="center">
                <template #default="scope">
                  <div class="action-buttons">
                    <el-button 
                      v-if="scope.row.username !== 'admin'"
                      :type="scope.row.is_active ? 'warning' : 'success'"
                      size="small"
                      @click="toggleUser(scope.row)"
                      class="action-btn"
                    >
                      <el-icon><Lock v-if="scope.row.is_active" /><Unlock v-else /></el-icon>
                      {{ scope.row.is_active ? '禁用' : '启用' }}
                    </el-button>
                    <el-button 
                      v-if="scope.row.username !== 'admin'"
                      type="danger"
                      size="small"
                      @click="deleteUser(scope.row)"
                      class="action-btn"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 历史记录管理 -->
      <el-tab-pane label="历史记录管理" name="history">
        <div class="management-section">
          <el-card class="management-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon class="section-icon"><Document /></el-icon>
                  <span class="section-title">历史记录管理</span>
                </div>
                <div class="header-actions">
                  <el-button type="primary" @click="refreshHistory" :loading="historyLoading">
                    <el-icon><Refresh /></el-icon>
                    刷新记录
                  </el-button>
                  <el-button type="warning" @click="clearHistory('today')">
                    <el-icon><Calendar /></el-icon>
                    清理今日记录
                  </el-button>
                  <el-button type="danger" @click="clearHistory('all')">
                    <el-icon><Delete /></el-icon>
                    清理所有记录
                  </el-button>
                </div>
              </div>
            </template>
            
            <el-table :data="historyRecords" style="width: 100%" v-loading="historyLoading" class="modern-table">
              <el-table-column prop="图片名" label="图片名" width="200">
                <template #default="scope">
                  <div class="file-info">
                    <el-icon class="file-icon"><Picture /></el-icon>
                    <span class="filename">{{ scope.row.图片名 }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="车牌号" label="车牌号" width="120" align="center">
                <template #default="scope">
                  <el-tag v-if="scope.row.车牌号" type="primary" effect="dark">
                    {{ scope.row.车牌号 }}
                  </el-tag>
                  <span v-else class="no-data">未检测到</span>
                </template>
              </el-table-column>
              <el-table-column prop="车牌颜色" label="车牌颜色" width="100" align="center">
                <template #default="scope">
                  <el-tag v-if="scope.row.车牌颜色" :type="getPlateColorType(scope.row.车牌颜色)" effect="dark">
                    {{ scope.row.车牌颜色 }}
                  </el-tag>
                  <span v-else class="no-data">未检测到</span>
                </template>
              </el-table-column>
              <el-table-column prop="置信度" label="置信度" width="150" align="center">
                <template #default="scope">
                  <div v-if="scope.row.置信度 && scope.row.置信度 !== '0'" class="confidence-display-admin">
                    <el-progress 
                      :percentage="getConfidencePercentage(scope.row.置信度)" 
                      :color="getConfidenceColor(scope.row.置信度)"
                      :show-text="false"
                      :stroke-width="8"
                    />
                    <span class="confidence-text-admin">{{ formatConfidence(scope.row.置信度) }}</span>
                  </div>
                  <span v-else class="no-data">未检测到</span>
                </template>
              </el-table-column>
              <el-table-column prop="识别时间" label="识别时间" width="180" align="center"></el-table-column>
              <el-table-column prop="date" label="日期" width="120" align="center">
                <template #default="scope">
                  <el-tag type="info" effect="plain">{{ scope.row.date }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- AI对话组件 -->
    <AiChat v-model="aiChatVisible" />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { 
  Setting, 
  User, 
  DataAnalysis, 
  TrendCharts, 
  Refresh, 
  Crown, 
  CircleCheck, 
  CircleClose, 
  Lock, 
  Unlock, 
  Delete, 
  Document, 
  Calendar, 
  Picture,
  ChatDotRound
} from '@element-plus/icons-vue'
import AiChat from '@/components/AiChat.vue'

export default {
  name: 'Admin',
  components: {
    AiChat
  },
  setup() {
    const router = useRouter()
    const activeTab = ref('statistics')
    const currentUser = ref({})
    const statistics = ref({
      users: { total: 0, active: 0, admin: 0 },
      detections: { today: 0, today_successful: 0, all_time: 0 }
    })
    const users = ref([])
    const usersLoading = ref(false)
    const historyRecords = ref([])
    const historyLoading = ref(false)
    const aiChatVisible = ref(false)

    // 检查管理员权限
    const checkAdminPermission = () => {
      const userInfo = localStorage.getItem('userInfo')
      if (!userInfo) {
        ElMessage.error('请先登录')
        router.push('/login')
        return false
      }
      
      const user = JSON.parse(userInfo)
      if (user.role !== 'admin') {
        ElMessage.error('权限不足，需要管理员权限')
        router.push('/')
        return false
      }
      
      currentUser.value = user
      return true
    }

    // 获取统计信息
    const getStatistics = async () => {
      try {
        const response = await axios.post('admin/statistics', {
          admin_username: currentUser.value.username
        })
        if (response.data.status === 'success') {
          statistics.value = response.data.statistics
        }
      } catch (error) {
        ElMessage.error('获取统计信息失败')
      }
    }

    // 获取用户列表
    const getUsers = async () => {
      usersLoading.value = true
      try {
        const response = await axios.post('admin/users', {
          admin_username: currentUser.value.username
        })
        if (response.data.status === 'success') {
          users.value = response.data.users
        }
      } catch (error) {
        ElMessage.error('获取用户列表失败')
      } finally {
        usersLoading.value = false
      }
    }

    // 获取历史记录
    const getHistory = async () => {
      historyLoading.value = true
      try {
        const response = await axios.post('admin/all_history', {
          admin_username: currentUser.value.username
        })
        if (response.data.status === 'success') {
          historyRecords.value = response.data.records
        }
      } catch (error) {
        ElMessage.error('获取历史记录失败')
      } finally {
        historyLoading.value = false
      }
    }

    // 切换用户状态
    const toggleUser = async (user) => {
      try {
        const action = user.is_active ? '禁用' : '启用'
        await ElMessageBox.confirm(`确定要${action}用户 ${user.username} 吗？`, '确认操作')
        
        const response = await axios.post('admin/toggle_user', {
          admin_username: currentUser.value.username,
          user_id: user.id
        })
        
        if (response.data.status === 'success') {
          ElMessage.success(response.data.message)
          await getUsers()
          await getStatistics()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
      }
    }

    // 删除用户
    const deleteUser = async (user) => {
      try {
        await ElMessageBox.confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复！`, '确认删除', {
          type: 'warning'
        })
        
        const response = await axios.post('admin/delete_user', {
          admin_username: currentUser.value.username,
          user_id: user.id
        })
        
        if (response.data.status === 'success') {
          ElMessage.success(response.data.message)
          await getUsers()
          await getStatistics()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    // 清理历史记录
    const clearHistory = async (type) => {
      try {
        const typeText = type === 'today' ? '今日' : '所有'
        await ElMessageBox.confirm(`确定要清理${typeText}历史记录吗？此操作不可恢复！`, '确认清理', {
          type: 'warning'
        })
        
        const response = await axios.post('admin/clear_history', {
          admin_username: currentUser.value.username,
          clear_type: type
        })
        
        if (response.data.status === 'success') {
          ElMessage.success(response.data.message)
          await getHistory()
          await getStatistics()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清理失败')
        }
      }
    }

    // 刷新函数
    const refreshStatistics = () => getStatistics()
    const refreshUsers = () => getUsers()
    const refreshHistory = () => getHistory()

    // 计算成功率
    const getSuccessRate = () => {
      const { today, today_successful } = statistics.value.detections
      if (today === 0) return 0
      return Math.round((today_successful / today) * 100)
    }

    // 获取车牌颜色类型
    const getPlateColorType = (color) => {
      const colorMap = {
        '蓝': 'primary',
        '黄': 'warning',
        '绿': 'success',
        '白': 'info',
        '黑': 'info'
      }
      return colorMap[color] || 'info'
    }

    // 置信度处理函数
    const getConfidencePercentage = (confidence) => {
      if (confidence === null || confidence === undefined || confidence === '' || confidence === '未检测到' || confidence === '0') {
        return 0
      }
      const num = typeof confidence === 'string' ? parseFloat(confidence) : confidence
      if (isNaN(num)) return 0
      return Math.round(num * 100)
    }

    const getConfidenceColor = (confidence) => {
      if (confidence === null || confidence === undefined || confidence === '' || confidence === '未检测到' || confidence === '0') {
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
      if (confidence === null || confidence === undefined || confidence === '' || confidence === '未检测到' || confidence === '0') {
        return '未检测到'
      }
      const num = typeof confidence === 'string' ? parseFloat(confidence) : confidence
      if (isNaN(num)) return '未检测到'
      return `${(num * 100).toFixed(2)}%`
    }

    // 显示AI对话
    const showAiChat = () => {
      aiChatVisible.value = true
    }

    onMounted(async () => {
      if (checkAdminPermission()) {
        await getStatistics()
        await getUsers()
        await getHistory()
      }
    })

    return {
      activeTab,
      currentUser,
      statistics,
      users,
      usersLoading,
      historyRecords,
      historyLoading,
      aiChatVisible,
      toggleUser,
      deleteUser,
      clearHistory,
      refreshStatistics,
      refreshUsers,
      refreshHistory,
      getSuccessRate,
      getPlateColorType,
      getConfidencePercentage,
      getConfidenceColor,
      formatConfidence,
      showAiChat,
      ChatDotRound
    }
  }
}
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

/* 页面头部样式 */
.admin-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 30px 40px;
  margin-bottom: 30px;
  color: white;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 36px;
  color: white;
}

.header-title h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 1px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ai-chat-btn {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 25px;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
  transition: all 0.3s ease;
}

.ai-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
  background: linear-gradient(135deg, #ee5a24 0%, #ff6b6b 100%);
}

.user-avatar {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 600;
}

.user-info {
  text-align: right;
}

.welcome-text {
  font-size: 14px;
  opacity: 0.9;
  margin: 0 0 4px 0;
}

.username {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

/* 标签页样式 */
.admin-tabs {
  max-width: 1200px;
  margin: 0 auto;
}

:deep(.el-tabs__header) {
  margin-bottom: 30px;
}

:deep(.el-tabs__nav) {
  border: none;
}

:deep(.el-tabs__item) {
  border: none;
  background: white;
  margin-right: 8px;
  border-radius: 12px 12px 0 0;
  padding: 0 24px;
  font-weight: 600;
  transition: all 0.3s ease;
}

:deep(.el-tabs__item.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

:deep(.el-tabs__content) {
  padding: 0;
}

/* 统计卡片样式 */
.statistics-section {
  padding: 0;
}

.stat-card {
  border-radius: 20px;
  border: none;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 200px;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.users-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.detection-card {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

.history-card {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  color: white;
}

.stat-item {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 20px;
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-content h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 16px 0;
  opacity: 0.9;
}

.stat-numbers {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-number {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-number .number {
  font-size: 24px;
  font-weight: 700;
}

.stat-number .label {
  font-size: 14px;
  opacity: 0.8;
}

.refresh-btn {
  margin-top: 16px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 管理卡片样式 */
.management-section {
  padding: 0;
}

.management-card {
  border-radius: 20px;
  border: none;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

:deep(.management-card .el-card__header) {
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  padding: 20px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  font-size: 24px;
  color: #667eea;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 表格样式 */
.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.modern-table .el-table__header) {
  background: #f8f9fa;
}

:deep(.modern-table .el-table th) {
  background: #f8f9fa;
  color: #333;
  font-weight: 600;
  border-bottom: 1px solid #e9ecef;
}

:deep(.modern-table .el-table td) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 12px;
}

:deep(.modern-table .el-table__row:hover) {
  background: #f8f9fa;
}

/* 用户信息样式 */
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar-small {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
}

.username {
  font-weight: 500;
  color: #333;
}

/* 文件信息样式 */
.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #667eea;
  font-size: 16px;
}

.filename {
  font-weight: 500;
  color: #333;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-btn {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

/* 置信度显示样式 */
.confidence-display-admin {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.confidence-display-admin .el-progress {
  width: 60px;
}

.confidence-text-admin {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  min-width: 60px;
}

/* 无数据样式 */
.no-data {
  color: #999;
  font-style: italic;
  font-size: 12px;
}

/* 按钮样式覆盖 */
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

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
}

/* 标签样式 */
:deep(.el-tag) {
  border-radius: 8px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 进度条样式 */
:deep(.el-progress-bar__outer) {
  border-radius: 6px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-container {
    padding: 10px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .stat-item {
    flex-direction: column;
    text-align: center;
  }
  
  .stat-icon {
    margin-right: 0;
    margin-bottom: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>