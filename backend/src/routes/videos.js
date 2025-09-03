const express = require('express');
const { body, validationResult } = require('express-validator');
const Video = require('../models/Video');
const { auth, optionalAuth } = require('../middleware/auth');

const router = express.Router();

router.post('/', auth, [
  body('title').trim().isLength({ min: 1, max: 200 }).withMessage('标题长度为1-200个字符'),
  body('description').optional().trim().isLength({ max: 2000 }).withMessage('描述最多2000个字符')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { title, description, projectData } = req.body;

    const video = new Video({
      title,
      description,
      user: req.user._id,
      projectData: projectData || {
        scenes: [],
        timeline: { totalDuration: 0, fps: 30, resolution: { width: 1920, height: 1080 } },
        assets: []
      }
    });

    await video.save();

    res.status(201).json({
      message: '视频项目创建成功',
      video
    });
  } catch (error) {
    console.error('Create video error:', error);
    res.status(500).json({ error: '创建视频项目失败' });
  }
});

router.get('/', auth, async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;
    const status = req.query.status;

    const filter = { user: req.user._id };
    if (status) {
      filter.status = status;
    }

    const videos = await Video.find(filter)
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);

    const total = await Video.countDocuments(filter);

    res.json({
      videos,
      pagination: {
        current: page,
        total: Math.ceil(total / limit),
        count: videos.length,
        totalItems: total
      }
    });
  } catch (error) {
    console.error('Get videos error:', error);
    res.status(500).json({ error: '获取视频列表失败' });
  }
});

router.get('/:id', [auth, optionalAuth], async (req, res) => {
  try {
    const video = await Video.findById(req.params.id);

    if (!video) {
      return res.status(404).json({ error: '视频项目不存在' });
    }

    if (!video.isPublic && (!req.user || video.user.toString() !== req.user._id.toString())) {
      return res.status(403).json({ error: '无权访问此视频项目' });
    }

    if (video.isPublic && req.user && video.user.toString() !== req.user._id.toString()) {
      video.views += 1;
      await video.save();
    }

    res.json({ video });
  } catch (error) {
    console.error('Get video error:', error);
    res.status(500).json({ error: '获取视频项目失败' });
  }
});

router.put('/:id', auth, async (req, res) => {
  try {
    const video = await Video.findById(req.params.id);

    if (!video) {
      return res.status(404).json({ error: '视频项目不存在' });
    }

    if (video.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ error: '无权修改此视频项目' });
    }

    const updates = {};
    const allowedFields = ['title', 'description', 'projectData', 'exportSettings', 'status', 'tags', 'isPublic'];
    
    allowedFields.forEach(field => {
      if (req.body[field] !== undefined) {
        updates[field] = req.body[field];
      }
    });

    const updatedVideo = await Video.findByIdAndUpdate(
      req.params.id,
      { $set: updates },
      { new: true }
    );

    res.json({
      message: '视频项目更新成功',
      video: updatedVideo
    });
  } catch (error) {
    console.error('Update video error:', error);
    res.status(500).json({ error: '更新视频项目失败' });
  }
});

router.delete('/:id', auth, async (req, res) => {
  try {
    const video = await Video.findById(req.params.id);

    if (!video) {
      return res.status(404).json({ error: '视频项目不存在' });
    }

    if (video.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ error: '无权删除此视频项目' });
    }

    await Video.findByIdAndDelete(req.params.id);

    res.json({ message: '视频项目删除成功' });
  } catch (error) {
    console.error('Delete video error:', error);
    res.status(500).json({ error: '删除视频项目失败' });
  }
});

router.post('/:id/duplicate', auth, async (req, res) => {
  try {
    const originalVideo = await Video.findById(req.params.id);

    if (!originalVideo) {
      return res.status(404).json({ error: '视频项目不存在' });
    }

    if (originalVideo.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ error: '无权复制此视频项目' });
    }

    const duplicatedVideo = new Video({
      title: `${originalVideo.title} (副本)`,
      description: originalVideo.description,
      user: req.user._id,
      projectData: originalVideo.projectData,
      exportSettings: originalVideo.exportSettings,
      tags: originalVideo.tags,
      status: 'draft'
    });

    await duplicatedVideo.save();

    res.status(201).json({
      message: '视频项目复制成功',
      video: duplicatedVideo
    });
  } catch (error) {
    console.error('Duplicate video error:', error);
    res.status(500).json({ error: '复制视频项目失败' });
  }
});

module.exports = router;