import axios from 'axios'

// Electron API 接口类型定义
declare global {
  interface Window {
    electronAPI: {
      getAppVersion: () => Promise<string>
      getSystemInfo: () => Promise<any>
      getSettings: () => Promise<any>
      updateSettings: (key: string, value: any) => Promise<void>
      getRecentProjects: () => Promise<any[]>
      addRecentProject: (project: any) => Promise<void>
      removeRecentProject: (path: string) => Promise<void>
      showOpenDialog: (options: any) => Promise<any>
      showSaveDialog: (options: any) => Promise<any>
      showMessageBox: (options: any) => Promise<any>
      openExternal: (url: string) => Promise<void>
      openPath: (path: string) => Promise<void>
      readFile: (filePath: string) => Promise<any>
      writeFile: (filePath: string, content: string) => Promise<any>
      deleteFile: (filePath: string) => Promise<any>
      createDirectory: (dirPath: string) => Promise<any>
      readDirectory: (dirPath: string) => Promise<any>
      minimizeWindow: () => Promise<void>
      maximizeWindow: () => Promise<void>
      closeWindow: () => Promise<void>
      checkForUpdates: () => Promise<void>
      quitAndInstall: () => Promise<void>
    }
  }
}

// 初始化 Electron API
export const initElectronAPI = () => {
  if (window.electronAPI) {
    return window.electronAPI
  }
  
  // 开发环境下的模拟 API
  return {
    getAppVersion: () => Promise.resolve('1.0.0'),
    getSystemInfo: () => Promise.resolve({
      platform: 'darwin',
      arch: 'x64',
      version: 'v18.0.0'
    }),
    getSettings: () => Promise.resolve({
      general: { theme: 'light', language: 'zh-CN' },
      editor: { autoSave: true }
    }),
    updateSettings: (key: string, value: any) => Promise.resolve(),
    getRecentProjects: () => Promise.resolve([]),
    addRecentProject: (project: any) => Promise.resolve(),
    removeRecentProject: (path: string) => Promise.resolve(),
    showOpenDialog: (options: any) => Promise.resolve({ filePaths: [] }),
    showSaveDialog: (options: any) => Promise.resolve({ filePath: '' }),
    showMessageBox: (options: any) => Promise.resolve({ response: 0 }),
    openExternal: (url: string) => Promise.resolve(),
    openPath: (path: string) => Promise.resolve(),
    readFile: (filePath: string) => Promise.resolve({ success: true, content: '' }),
    writeFile: (filePath: string, content: string) => Promise.resolve({ success: true }),
    deleteFile: (filePath: string) => Promise.resolve({ success: true }),
    createDirectory: (dirPath: string) => Promise.resolve({ success: true }),
    readDirectory: (dirPath: string) => Promise.resolve({ success: true, files: [] }),
    minimizeWindow: () => Promise.resolve(),
    maximizeWindow: () => Promise.resolve(),
    closeWindow: () => Promise.resolve(),
    checkForUpdates: () => Promise.resolve(),
    quitAndInstall: () => Promise.resolve()
  }
}

export const electronAPI = initElectronAPI()