const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  // 开发服务器配置
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5002',
        changeOrigin: true
      }
    }
  },
  // 生产环境配置
  productionSourceMap: false,
  // 输出目录配置
  outputDir: 'dist',
  // 静态资源目录
  assetsDir: 'static'
})