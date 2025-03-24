// app.js
const api = require('./api.js')

App({
  globalData: {
    userInfo: null,
    isLoggedIn: false
  },
  
  onLaunch: function() {
    // 检查是否有登录状态
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    
    if (token && userInfo) {
      this.globalData.userInfo = userInfo
      this.globalData.isLoggedIn = true
    }
  },
  
  // 微信登录
  login: async function() {
    try {
      const { code } = await wx.login()
      if (!code) {
        throw new Error('微信登录失败')
      }
      
      const loginResult = await api.login(code)
      if (loginResult.token) {
        wx.setStorageSync('token', loginResult.token)
        wx.setStorageSync('userInfo', loginResult.userInfo)
        this.globalData.userInfo = loginResult.userInfo
        this.globalData.isLoggedIn = true
        return loginResult
      } else {
        throw new Error(loginResult.message || '登录失败')
      }
    } catch (error) {
      console.error('登录失败:', error)
      wx.showToast({
        title: error.message || '登录失败',
        icon: 'none'
      })
      return { success: false, message: error.message }
    }
  },
  
  // 更新用户资料
  updateUserInfo: async function(userInfo) {
    try {
      const result = await api.updateUserProfile(userInfo)
      if (result.success) {
        // 更新本地存储和全局数据
        const currentUserInfo = wx.getStorageSync('userInfo') || {}
        const updatedUserInfo = { ...currentUserInfo, ...userInfo }
        
        wx.setStorageSync('userInfo', updatedUserInfo)
        this.globalData.userInfo = updatedUserInfo
        return { success: true, userInfo: updatedUserInfo }
      } else {
        throw new Error(result.message || '更新失败')
      }
    } catch (error) {
      console.error('更新用户资料失败:', error)
      return { success: false, message: error.message }
    }
  }
})
