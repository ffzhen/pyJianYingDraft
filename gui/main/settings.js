const { app } = require('electron');
const path = require('path');
const fs = require('fs');

class AppSettings {
  constructor() {
    this.userDataPath = app.getPath('userData');
    this.settingsPath = path.join(this.userDataPath, 'settings.json');
    this.settings = this.loadSettings();
  }

  loadSettings() {
    try {
      if (fs.existsSync(this.settingsPath)) {
        const data = fs.readFileSync(this.settingsPath, 'utf8');
        return JSON.parse(data);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
    
    return this.getDefaultSettings();
  }

  getDefaultSettings() {
    return {
      general: {
        language: 'zh-CN',
        theme: 'system',
        autoUpdate: true,
        startup: true
      },
      editor: {
        autoSave: true,
        autoSaveInterval: 300000, // 5 minutes
        backupEnabled: true,
        backupCount: 5,
        defaultExportFormat: 'mp4',
        defaultExportQuality: 'high',
        defaultResolution: '1080p'
      },
      performance: {
        hardwareAcceleration: true,
        maxMemoryUsage: 2048, // MB
        cacheSize: 1024, // MB
        gpuAcceleration: true
      },
      network: {
        apiUrl: 'http://localhost:5000/api',
        timeout: 30000,
        retryAttempts: 3
      },
      window: {
        width: 1400,
        height: 900,
        maximized: false,
        fullscreen: false
      },
      projects: {
        defaultProjectPath: path.join(app.getPath('documents'), 'VideoDraft Projects'),
        recentProjects: [],
        autoRecover: true
      }
    };
  }

  saveSettings() {
    try {
      fs.writeFileSync(this.settingsPath, JSON.stringify(this.settings, null, 2));
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  }

  get(key) {
    const keys = key.split('.');
    let value = this.settings;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return undefined;
      }
    }
    
    return value;
  }

  set(key, value) {
    const keys = key.split('.');
    let current = this.settings;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      if (!(k in current) || typeof current[k] !== 'object') {
        current[k] = {};
      }
      current = current[k];
    }
    
    current[keys[keys.length - 1]] = value;
    return this.saveSettings();
  }

  delete(key) {
    const keys = key.split('.');
    let current = this.settings;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      if (!(k in current) || typeof current[k] !== 'object') {
        return false;
      }
      current = current[k];
    }
    
    if (keys[keys.length - 1] in current) {
      delete current[keys[keys.length - 1]];
      return this.saveSettings();
    }
    
    return false;
  }

  reset() {
    this.settings = this.getDefaultSettings();
    return this.saveSettings();
  }

  export() {
    return JSON.stringify(this.settings, null, 2);
  }

  import(settingsJson) {
    try {
      const imported = JSON.parse(settingsJson);
      this.settings = { ...this.getDefaultSettings(), ...imported };
      return this.saveSettings();
    } catch (error) {
      console.error('Failed to import settings:', error);
      return false;
    }
  }

  addRecentProject(projectPath, projectName) {
    const recentProjects = this.get('projects.recentProjects') || [];
    const existingIndex = recentProjects.findIndex(p => p.path === projectPath);
    
    if (existingIndex >= 0) {
      recentProjects.splice(existingIndex, 1);
    }
    
    recentProjects.unshift({
      path: projectPath,
      name: projectName,
      lastAccessed: new Date().toISOString()
    });
    
    // Keep only the last 10 projects
    if (recentProjects.length > 10) {
      recentProjects.splice(10);
    }
    
    return this.set('projects.recentProjects', recentProjects);
  }

  removeRecentProject(projectPath) {
    const recentProjects = this.get('projects.recentProjects') || [];
    const filteredProjects = recentProjects.filter(p => p.path !== projectPath);
    return this.set('projects.recentProjects', filteredProjects);
  }

  clearRecentProjects() {
    return this.set('projects.recentProjects', []);
  }

  getProjectPath() {
    const projectPath = this.get('projects.defaultProjectPath');
    if (!fs.existsSync(projectPath)) {
      fs.mkdirSync(projectPath, { recursive: true });
    }
    return projectPath;
  }

  ensureDirectories() {
    const directories = [
      this.getProjectPath(),
      path.join(this.userDataPath, 'cache'),
      path.join(this.userDataPath, 'temp'),
      path.join(this.userDataPath, 'backups'),
      path.join(this.userDataPath, 'logs')
    ];

    directories.forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }
}

module.exports = AppSettings;