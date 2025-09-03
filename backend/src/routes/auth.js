const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const User = require('../models/User');
const { auth } = require('../middleware/auth');

const router = express.Router();

const generateToken = (userId) => {
  return jwt.sign({ userId }, process.env.JWT_SECRET || 'your-secret-key', { expiresIn: '7d' });
};

router.post('/register', [
  body('username').trim().isLength({ min: 3, max: 30 }).withMessage('用户名长度为3-30个字符'),
  body('email').isEmail().normalizeEmail().withMessage('请输入有效的邮箱地址'),
  body('password').isLength({ min: 6 }).withMessage('密码至少6个字符')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { username, email, password } = req.body;

    const existingUser = await User.findOne({ 
      $or: [{ email }, { username }] 
    });

    if (existingUser) {
      return res.status(400).json({ error: '用户名或邮箱已存在' });
    }

    const user = new User({ username, email, password });
    await user.save();

    const token = generateToken(user._id);

    res.status(201).json({
      message: '注册成功',
      token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email,
        profile: user.profile,
        preferences: user.preferences
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: '注册失败，请稍后重试' });
  }
});

router.post('/login', [
  body('email').isEmail().normalizeEmail().withMessage('请输入有效的邮箱地址'),
  body('password').notEmpty().withMessage('密码不能为空')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password } = req.body;

    const user = await User.findOne({ email });
    if (!user || !user.isActive) {
      return res.status(400).json({ error: '邮箱或密码错误' });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(400).json({ error: '邮箱或密码错误' });
    }

    user.lastLogin = new Date();
    await user.save();

    const token = generateToken(user._id);

    res.json({
      message: '登录成功',
      token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email,
        profile: user.profile,
        preferences: user.preferences
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: '登录失败，请稍后重试' });
  }
});

router.get('/me', auth, async (req, res) => {
  try {
    res.json({
      user: {
        id: req.user._id,
        username: req.user.username,
        email: req.user.email,
        profile: req.user.profile,
        preferences: req.user.preferences,
        subscription: req.user.subscription
      }
    });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: '获取用户信息失败' });
  }
});

router.put('/profile', auth, [
  body('username').optional().trim().isLength({ min: 3, max: 30 }),
  body('firstName').optional().trim(),
  body('lastName').optional().trim(),
  body('bio').optional().isLength({ max: 500 })
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const updates = {};
    const allowedFields = ['username', 'firstName', 'lastName', 'bio', 'avatar'];
    
    allowedFields.forEach(field => {
      if (req.body[field] !== undefined) {
        if (field === 'firstName' || field === 'lastName') {
          updates[`profile.${field}`] = req.body[field];
        } else {
          updates[field] = req.body[field];
        }
      }
    });

    const user = await User.findByIdAndUpdate(
      req.user._id,
      { $set: updates },
      { new: true }
    ).select('-password');

    res.json({
      message: '个人资料更新成功',
      user
    });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: '更新个人资料失败' });
  }
});

router.post('/change-password', auth, [
  body('currentPassword').notEmpty().withMessage('当前密码不能为空'),
  body('newPassword').isLength({ min: 6 }).withMessage('新密码至少6个字符')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { currentPassword, newPassword } = req.body;
    const user = await User.findById(req.user._id);

    const isMatch = await user.comparePassword(currentPassword);
    if (!isMatch) {
      return res.status(400).json({ error: '当前密码错误' });
    }

    user.password = newPassword;
    await user.save();

    res.json({ message: '密码修改成功' });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ error: '密码修改失败' });
  }
});

module.exports = router;