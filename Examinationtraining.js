Page({
  data: {
    loading: false,
    apiBaseUrl: 'http://42.193.118.248:5000', // 修改API基础URL，移除/api
    userId: '', // 用户 ID，可从登录信息中获取
    activeType: 'kaoyan',
    activeYear: null,
    activeCategory: null,
    examTypes: [
      { type: 'kaoyan', name: '考研资料' },
      { type: 'gongkao', name: '公考资料' },
      { type: 'cet', name: '四六级' },
      { type: 'teacher', name: '教资' },
      { type: 'putonghua', name: '普通话' },
      { type: 'jiazzhao', name: '驾照' },
      { type: 'ncre', name: '计算机等级' }
    ],
    years: [2024, 2023, 2022, 2021, 2020],
    categories: {
      kaoyan: [
        { type: 'politics', name: '政治题库' },
        { type: 'english', name: '英语题库' },
        { type: 'math', name: '数学题库' }
      ],
      gongkao: [
        { type: 'xingce', name: '行测' },
        { type: 'shenlun', name: '申论' },
        { type: 'mianshi', name: '面试' }
      ],
      cet: [
        { type: 'cet4', name: '四级题库' },
        { type: 'cet6', name: '六级题库' }
      ],
      teacher: [
        { type: 'comprehensive', name: '综合素质' },
        { type: 'knowledge', name: '教育知识' }
      ],
      putonghua: [
        { type: 'theory', name: '理论知识' },
        { type: 'practice', name: '实践训练' }
      ],
      jiazzhao: [
        { type: 'science', name: '科目一' },
        { type: 'operation', name: '科目四' }
      ],
      ncre: [
        { type: 'level1', name: '一级题库' },
        { type: 'msoffice', name: 'MSOffice二级' },
        { type: 'wpsoffice', name: 'WPSOffice二级' }
      ]
    },
    examInfo: {
      kaoyan: {
        title: '考研重要信息',
        website: '中国研究生招生信息网',
        registrationTime: '每年10月上旬',
        examTime: '每年12月下旬',
        subjects: [
          '政治：必考科目',
          '英语：英语一(文、理、工)、英语二(经、管、医等)',
          '数学：数学一(理工)、数学二(经管)、数学三(文科)'
        ]
      },
      gongkao: {
        title: '公考重要信息',
        website: '中国人事考试网',
        registrationTime: '每年10月',
        examTime: '每年11月-12月',
        subjects: [
          '行政职业能力测验（行测）',
          '申论',
          '面试'
        ]
      },
      cet: {
        title: '四六级考试信息',
        website: '中国教育考试网',
        registrationTime: '每年3月/9月',
        examTime: '每年6月/12月',
        subjects: [
          '听力',
          '阅读理解',
          '翻译和写作'
        ]
      },
      teacher: {
        title: '教师资格证考试信息',
        website: '中国教育考试网',
        registrationTime: '每年3月/9月',
        examTime: '每年3月/11月',
        subjects: [
          '综合素质',
          '教育知识与能力',
          '学科知识与教学能力'
        ]
      },
      putonghua: {
        title: '普通话水平测试信息',
        website: '普通话水平测试网',
        registrationTime: '全年常开',
        
        examTime: '预约后安排',
        subjects: [
          '声母',
          '韵母',
          '声调',
          '朗读短文',
          '命题说话'
        ]
      },
      jiazzhao: {
        title: '驾驶证考试信息',
        website: '车管所官网',
        registrationTime: '全年常开',
        examTime: '预约后安排',
        subjects: [
          '科目一：交通法规理论考试',
          '科目二：场地驾驶技能考试',
          '科目三：道路驾驶技能考试',
          '科目四：安全文明驾驶常识考试'
        ]
      },
      ncre: {
        title: '计算机等级考试信息',
        website: '中国教育考试网',
        registrationTime: '每年3月/9月',
        examTime: '每年3月/9月',
        subjects: [
          '计算机基础及MS Office应用',
          'Python语言程序设计',
          '数据库技术',
          '网络安全技术'
        ]
      }
    },
    resources: [], // 资源列表
    filteredResources: [], // 筛选后的资源列表
    downloadedFiles: [], // 用户下载历史
    isFavorite: {} // 是否收藏，使用资源 ID 作为键
  },

  onLoad() {
    // 获取登录用户 ID，这里假设已经登录并保存在本地存储中
    let userId = wx.getStorageSync('userId') || '';
    
    // 如果没有用户ID，则设置一个默认的测试用户ID
    if (!userId) {
      userId = 'test_user_001';
      wx.setStorageSync('userId', userId);
    }
    
    this.setData({ userId });
    console.log('当前用户ID:', userId);
    
    this.loadResources();
    this.loadUserFavorites();
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadResources().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 加载用户收藏
  async loadUserFavorites() {
    if (!this.data.userId) return;
    
    try {
      return new Promise((resolve, reject) => {
        wx.request({
          url: `${this.data.apiBaseUrl}/api/exam/favorites?user_id=${this.data.userId}`,
          method: 'GET',
          header: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          success: (response) => {
            console.log('加载收藏响应:', response);
            if (response.statusCode === 200 && response.data && response.data.code === 0 && response.data.data) {
              const favorites = {};
              response.data.data.forEach(item => {
                favorites[item.id] = true;
              });
              
              this.setData({ isFavorite: favorites });
              resolve(favorites);
            } else {
              console.warn('加载收藏返回无效数据:', response);
              resolve({});
            }
          },
          fail: (err) => {
            console.error('加载收藏网络请求失败:', err);
            resolve({}); // 失败时返回空对象，不影响主流程
          }
        });
      });
    } catch (error) {
      console.error('加载收藏失败:', error);
      return {};
    }
  },

  // 加载资源列表
  async loadResources() {
    this.setData({ loading: true });
    try {
      // 构建查询参数
      const params = {
        exam_type: this.data.activeType
      };

      if (this.data.activeYear) {
        params.year = this.data.activeYear;
      }
      
      if (this.data.activeCategory) {
        params.category = this.data.activeCategory;
      }
      
      // 添加用户ID，用于获取收藏状态
      if (this.data.userId) {
        params.user_id = this.data.userId;
      }

      // 将参数转换为查询字符串
      const queryString = Object.keys(params)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
        .join('&');

      // 记录请求URL
      const requestUrl = `${this.data.apiBaseUrl}/api/exam/resources?${queryString}`;
      console.log('请求URL:', requestUrl);

      // 发送请求到API
      return new Promise((resolve, reject) => {
        wx.request({
          url: requestUrl,
          method: 'GET',
          header: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          success: (response) => {
            console.log('API响应详情:', response);
            if (response.statusCode === 200 && response.data && response.data.code === 0) {
              const responseData = response.data.data || [];
              console.log('获取到资源数据:', responseData);
              
              if (responseData.length === 0) {
                console.log('没有找到资源数据');
                this.setData({ 
                  resources: [],
                  filteredResources: [],
                  loading: false
                });
                resolve([]);
                return;
              }
              
              // 处理API返回的数据
              const resources = responseData.map(item => ({
                id: item.id,
                title: item.title || '未命名资源',
                description: item.description || '暂无描述',
                fileType: item.file_type || 'pdf',
                fileSize: this.formatFileSize(item.file_size || 0),
                downloadCount: item.download_count || 0,
                year: item.year || 2024,
                category: item.category || '',
                examType: item.exam_type || this.data.activeType,
                fileId: item.file_id || '', // 用于下载的文件ID
                isFavorite: item.is_favorite || false // 是否已收藏
              }));

              console.log('格式化后的资源:', resources);

              // 更新收藏状态
              const favoriteStatus = {};
              resources.forEach(item => {
                if (item.isFavorite) {
                  favoriteStatus[item.id] = true;
                }
              });

              this.setData({ 
                resources,
                filteredResources: resources,
                loading: false,
                isFavorite: favoriteStatus
              });
              resolve(resources);
            } else {
              console.error('API返回错误:', response.data);
              const error = new Error(response.data?.message || '获取资源失败');
              this.setData({ loading: false });
              reject(error);
            }
          },
          fail: (err) => {
            console.error('请求失败:', err);
            const error = new Error('网络请求失败');
            this.setData({ loading: false });
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('加载资源失败:', error);
      
      wx.showToast({
        title: '加载失败',
        icon: 'error'
      });
      
      this.setData({ loading: false });
    }
  },

  // 格式化文件大小
  formatFileSize(size) {
    if (size < 1024) {
      return size + 'B';
    } else if (size < 1024 * 1024) {
      return (size / 1024).toFixed(2) + 'KB';
    } else {
      return (size / (1024 * 1024)).toFixed(2) + 'MB';
    }
  },

  // 切换主标签
  switchTab(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({
      activeType: type,
      activeYear: null,
      activeCategory: null
    });
    this.loadResources();
  },

  // 选择年份
  selectYear(e) {
    const year = e.currentTarget.dataset.year;
    this.setData({
      activeYear: this.data.activeYear === year ? null : year
    });
    this.filterResources();
  },

  // 选择类别
  selectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      activeCategory: this.data.activeCategory === category ? null : category
    });
    this.filterResources();
  },

  // 筛选资源
  filterResources() {
    const { activeYear, activeCategory, resources } = this.data;
    
    const filtered = resources.filter(resource => {
      const yearMatch = !activeYear || resource.year === activeYear;
      const categoryMatch = !activeCategory || resource.category === activeCategory;
      return yearMatch && categoryMatch;
    });

    this.setData({ filteredResources: filtered });
  },

  // 处理下载/预览
  handleDownload(e) {
    const resourceId = e.currentTarget.dataset.id;
    const resource = this.data.resources.find(r => r.id === resourceId);
    
    if (!resource) {
      wx.showToast({
        title: '资源不存在',
        icon: 'error'
      });
      return;
    }
    
    try {
      wx.showLoading({ title: '准备下载...' });
      
      // 向API请求下载链接 - 输出请求信息进行调试
      const requestData = {
        resource_id: resourceId,
        user_id: this.data.userId || 'anonymous'
      };
      console.log('下载请求参数:', requestData);
      
      // 使用回调方式进行请求
      wx.request({
        url: `${this.data.apiBaseUrl}/api/exam/download`,
        method: 'POST',
        data: requestData,
        header: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        success: (response) => {
          console.log('下载API响应详情:', response);
          
          if (response.statusCode !== 200 || response.data.code !== 0 || !response.data.data || !response.data.data.download_url) {
            console.error('API返回错误数据:', response.data);
            wx.hideLoading();
            wx.showToast({
              title: '获取下载链接失败',
              icon: 'error'
            });
            return;
          }
          
          const downloadUrl = response.data.data.download_url;
          const fileName = response.data.data.file_name;
          const fileType = response.data.data.file_type;
          
          console.log('准备下载文件:', {downloadUrl, fileName, fileType});
          
          wx.showLoading({ title: '下载中...' });
          
          // 下载文件到本地临时文件
          const downloadTask = wx.downloadFile({
            url: downloadUrl,
            success: (res) => {
              console.log('下载结果:', res);
              if (res.statusCode === 200) {
                wx.hideLoading();
                
                // 打开文件预览
                wx.openDocument({
                  filePath: res.tempFilePath,
                  fileType: fileType.toLowerCase(),
                  showMenu: true,
                  success: () => {
                    console.log('打开文档成功');
                    
                    // 更新资源下载次数（UI更新）
                    const resources = [...this.data.resources];
                    const index = resources.findIndex(r => r.id === resourceId);
                    if (index !== -1) {
                      resources[index].downloadCount += 1;
                      this.setData({ 
                        resources,
                        filteredResources: this.filterResourcesByCurrentCriteria(resources)
                      });
                    }
                  },
                  fail: (err) => {
                    console.error('打开文件失败:', err);
                    wx.showToast({
                      title: '打开失败',
                      icon: 'error'
                    });
                  }
                });
              } else {
                wx.hideLoading();
                wx.showToast({
                  title: '下载文件失败',
                  icon: 'error'
                });
              }
            },
            fail: (err) => {
              console.error('下载失败:', err);
              wx.hideLoading();
              wx.showToast({
                title: '下载失败',
                icon: 'error'
              });
            }
          });
          
          // 添加下载进度监听
          downloadTask.onProgressUpdate((res) => {
            wx.showLoading({
              title: `下载中 ${res.progress}%`,
            });
          });
        },
        fail: (err) => {
          console.error('API请求失败:', err);
          wx.hideLoading();
          wx.showToast({
            title: '请求失败',
            icon: 'error'
          });
        }
      });
      
    } catch (error) {
      console.error('处理失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '加载失败',
        icon: 'error'
      });
    }
  },
  
  // 辅助函数：根据当前筛选条件过滤资源
  filterResourcesByCurrentCriteria(resources) {
    const { activeYear, activeCategory } = this.data;
    
    if (!resources || !Array.isArray(resources)) {
      console.error('无效的资源数组:', resources);
      return [];
    }

    return resources.filter(resource => {
      if (!resource) return false;
      
      const yearMatch = !activeYear || resource.year == activeYear; // 使用宽松比较
      const categoryMatch = !activeCategory || resource.category === activeCategory;
      
      return yearMatch && categoryMatch;
    });
  },

  // 添加收藏
  async toggleFavorite(e) {
    if (!this.data.userId) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    const resourceId = e.currentTarget.dataset.id;
    const isFavorite = this.data.isFavorite[resourceId];
    
    try {
      // 发送收藏请求
      const requestData = {
        resource_id: resourceId,
        user_id: this.data.userId,
        action: isFavorite ? 'remove' : 'add'
      };
      
      console.log('收藏操作请求:', requestData);
      
      const response = await wx.request({
        url: `${this.data.apiBaseUrl}/api/exam/favorite`,
        method: 'POST',
        data: requestData
      });
      
      console.log('收藏操作响应:', response);
      
      if (response.statusCode !== 200 || response.data.code !== 0) {
        throw new Error(response.data?.message || '操作失败');
      }
      
      // 更新本地收藏状态
      const newIsFavorite = { ...this.data.isFavorite };
      if (isFavorite) {
        delete newIsFavorite[resourceId];
      } else {
        newIsFavorite[resourceId] = true;
      }
      
      this.setData({ isFavorite: newIsFavorite });
      
      wx.showToast({
        title: isFavorite ? '已取消收藏' : '已收藏',
        icon: 'success'
      });
    } catch (error) {
      console.error('收藏操作失败:', error);
      wx.showToast({
        title: '操作失败',
        icon: 'error'
      });
    }
  },

  // 跳转到我的收藏页面
  navigateToMyDownloads() {
    wx.navigateTo({
      url: '/pages/mydownload/mydownload?userId=' + (this.data.userId || ''),
      fail: function(err) {
        console.error('导航失败:', err);
        wx.showToast({
          title: '页面跳转失败',
          icon: 'none'
        });
      }
    });
  }
});