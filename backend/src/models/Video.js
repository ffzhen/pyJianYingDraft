const mongoose = require('mongoose');

const videoSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true,
    trim: true,
    maxlength: 200
  },
  description: {
    type: String,
    maxlength: 2000
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  projectData: {
    scenes: [{
      id: { type: String, required: true },
      title: { type: String, required: true },
      duration: { type: Number, required: true },
      elements: [{
        type: { type: String, enum: ['text', 'image', 'video', 'audio'] },
        content: { type: String },
        position: { x: Number, y: Number },
        size: { width: Number, height: Number },
        startTime: Number,
        endTime: Number
      }]
    }],
    timeline: {
      totalDuration: { type: Number, default: 0 },
      fps: { type: Number, default: 30 },
      resolution: { width: Number, height: Number }
    },
    assets: [{
      id: { type: String, required: true },
      name: { type: String, required: true },
      type: { type: String, enum: ['video', 'audio', 'image'], required: true },
      url: { type: String, required: true },
      size: { type: Number },
      duration: { type: Number }
    }]
  },
  exportSettings: {
    format: { type: String, enum: ['mp4', 'mov', 'avi'], default: 'mp4' },
    quality: { type: String, enum: ['low', 'medium', 'high'], default: 'medium' },
    resolution: { type: String, enum: ['720p', '1080p', '4k'], default: '1080p' }
  },
  status: {
    type: String,
    enum: ['draft', 'rendering', 'completed', 'failed'],
    default: 'draft'
  },
  tags: [{ type: String, trim: true }],
  isPublic: { type: Boolean, default: false },
  views: { type: Number, default: 0 },
  likes: { type: Number, default: 0 }
}, {
  timestamps: true
});

videoSchema.index({ user: 1, createdAt: -1 });
videoSchema.index({ status: 1 });
videoSchema.index({ tags: 1 });

module.exports = mongoose.model('Video', videoSchema);