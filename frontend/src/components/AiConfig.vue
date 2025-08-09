<template>
  <el-dialog
    v-model="visible"
    title="AI配置设置"
    width="600px"
    :before-close="handleClose"
    class="ai-config-dialog"
  >
    <div class="config-container">
      <div class="config-header">
        <el-icon class="config-icon"><Setting /></el-icon>
        <h3>GitHub模型配置</h3>
        <p>配置GitHub Personal Access Token以使用AI对话功能</p>
      </div>

      <el-form :model="configForm" :rules="rules" ref="configFormRef" label-width="120px">
        <el-form-item label="GitHub PAT" prop="githubToken">
          <el-input
            v-model="configForm.githubToken"
            type="password"
            placeholder="请输入GitHub Personal Access Token"
            show-password
            clearable
          />
          <div class="form-help">
            <el-text type="info" size="small">
              需要具有模型访问权限的GitHub PAT token
            </el-text>
          </div>
        </el-form-item>

        <el-form-item label="AI模型" prop="modelName">
          <el-select v-model="configForm.modelName" placeholder="选择AI模型">
            <el-option label="GPT-4o Mini" value="gpt-4o-mini" />
            <el-option label="GPT-4o" value="gpt-4o" />
            <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
          </el-select>
          <div class="form-help">
            <el-text type="info" size="small">
              推荐使用gpt-4o-mini，性价比更高
            </el-text>
          </div>
        </el-form-item>
      </el-form>

      <div class="config-help">
        <el-alert
          title="如何获取GitHub PAT?"
          type="info"
          :closable="false"
        >
          <template #default>
            <ol>
              <li>访问 <el-link href="https://github.com/settings/tokens" target="_blank">GitHub Settings > Personal access tokens</el-link></li>
              <li>点击 "Generate new token (classic)"</li>
              <li>设置token名称和过期时间</li>
              <li>确保勾选必要的权限范围</li>
              <li>生成token并复制到上方输入框</li>
            </ol>
          </template>
        </el-alert>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveConfig">
          保存配置
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import axios from 'axios'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'config-saved'])

// 响应式数据
const visible = ref(props.modelValue)
const saving = ref(false)
const configFormRef = ref(null)

const configForm = reactive({
  githubToken: '',
  modelName: 'gpt-4o-mini'
})

const rules = {
  githubToken: [
    { required: true, message: '请输入GitHub PAT token', trigger: 'blur' },
    { min: 10, message: 'Token长度至少10位', trigger: 'blur' }
  ],
  modelName: [
    { required: true, message: '请选择AI模型', trigger: 'change' }
  ]
}

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

const saveConfig = async () => {
  try {
    const valid = await configFormRef.value.validate()
    if (!valid) return

    saving.value = true

    const response = await axios.post('ai_config', {
      github_token: configForm.githubToken,
      model_name: configForm.modelName
    })

    if (response.data.status === 'success') {
      ElMessage.success('AI配置保存成功！')
      emit('config-saved')
      handleClose()
    } else {
      ElMessage.error(response.data.message || '配置保存失败')
    }
  } catch (error) {
    console.error('保存配置错误:', error)
    ElMessage.error('保存配置时发生错误')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.ai-config-dialog {
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

:deep(.el-dialog__body) {
  padding: 24px;
}

.config-container {
  max-width: 100%;
}

.config-header {
  text-align: center;
  margin-bottom: 24px;
}

.config-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.config-header h3 {
  color: #333;
  margin: 0 0 8px 0;
  font-size: 20px;
}

.config-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.form-help {
  margin-top: 4px;
}

.config-help {
  margin-top: 24px;
}

.config-help ol {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.config-help li {
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 600;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-alert) {
  border-radius: 8px;
}

:deep(.el-alert__content) {
  padding: 0;
}
</style>