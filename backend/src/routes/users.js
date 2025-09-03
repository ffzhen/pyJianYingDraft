const express = require('express');
const { body, validationResult } = require('express-validator');
const User = require('../models/User');
const Video = require('../models/Video');
const { auth } = require('../middleware/auth');

const router = express.Router();

router.get('/profile', auth, async (req, res) => {
  try {
    const user = await User.findById(req.user._id).select('-password');
    res.json({ user });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: '获取个人资料失败' });
  }
});

router.put('/preferences', auth, [
  body('theme').optional().isIn(['light', 'dark']),
  body('language').optional().isString(),
  body('notifications').optional().isBoolean()
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const updates = {};
    Object.keys(req.body).forEach(key => {
      updates[`preferences.${key}`] = req.body[key];
    });

    const user = await User.findByIdAndUpdate(
      req.user._id,
      { $set: updates },
      { new: true }
    ).select('-password');

    res.json({
      message: '偏好设置更新成功',
      user
    });
  } catch (error) {
    console.error('Update preferences error:', error);
    res.status(500).json({ error: '更新偏好设置失败' });
  }
});

router.get('/videos', auth, async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;

    const videos = await Video.find({ user: req.user._id })
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);

    const total = await Video.countDocuments({ user: req.user._id });

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
    console.error('Get user videos error:', error);
    res.status(500).json({ error: '获取视频列表失败' });
  }
});

router.get('/stats', auth, async (req, res) => {
  try {
    const totalVideos = await Video.countDocuments({ user: req.user._id });
    const completedVideos = await Video.countDocuments({ 
      user: req.user._id, 
      status: 'completed' 
    });
    const totalViews = await Video.aggregate([
      { $match: { user: req.user._id } },
      { $group: { _id: null, totalViews: { $sum: '$views' } } }
    ]);

    res.json({
      stats: {
        totalVideos,
        completedVideos,
        totalViews: totalViews[0]?.totalViews || 0,
        joinDate: req.user.createdAt
      }
    });
  } catch (error) {
    console.error('Get user stats error:', error);
    res.status(500).json({ error: '获取用户统计失败' });
  }
});

module.exports = router;