# -*- coding: utf-8 -*-
"""
===============================================================================
                       My-Links-in-1 - Bio Pages Server
                                الإصدار 2.0
===============================================================================
الوصف: خادم Flask مخصص لعرض صفحات البايو فقط
الخدمة: https://my-socials.onrender.com
المشروع: Social Media Analyzer Bot - النسخة الموحدة لجميع البوتات
===============================================================================
"""

import os
import logging
import sys
import json
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, jsonify, send_from_directory, request

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعدادات البيئة
PORT = int(os.environ.get('PORT', 10000))
RENDER_URL = os.environ.get('RENDER_URL', 'my-socials.onrender.com')

# =================================================================================
# 🔑 مفتاح API الموحد للبوتات
# =================================================================================
BIO_API_KEY = os.environ.get('BIO_API_KEY', 'bio_super_key_7x9k2m4p6q8r1s3t5u7w9y0z_A1B2C3D4E5F6')

# =================================================================================
# 🤖 قائمة البوتات المسموحة (Authorized Bots)
# =================================================================================
ALLOWED_BOTS = [
    'https://social-analyzer-bot-1.onrender.com',      # الإنتاج (Social_Media_tools_bot)
    'https://social-analyzer-bot-8.onrender.com',      # التطوير (Social_Analyzer_AI_bot)
    'https://social-analyzer-3.onrender.com',          # الاحتياطي (Social_Media_analyzer_bot)
    'https://api.telegram.org',                        # تلجرام API
    'https://t.me',                                    # تلجرام ويب
    'http://localhost:5000',                           # للتطوير المحلي
    'http://127.0.0.1:5000',                          # للتطوير المحلي
]

# إضافة مجلد utils للمسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد دوال قاعدة البيانات الخاصة بالبايو
from utils.db import get_bio_page_by_page_url, get_user_info, increment_bio_views

app = Flask(__name__)

# =================================================================================
# 🔒 دالة التحقق من صحة الطلب (Authentication)
# =================================================================================
def verify_request():
    """التحقق من أن الطلب قادم من بوت مسموح"""
    # طريقة 1: التحقق عبر API Key (الأكثر أماناً)
    api_key = request.headers.get('X-API-Key')
    if api_key and api_key == BIO_API_KEY:
        return True
    
    # طريقة 2: التحقق عبر Origin (للطلبات من المتصفح)
    origin = request.headers.get('Origin')
    if origin and origin in ALLOWED_BOTS:
        return True
    
    # طريقة 3: التحقق عبر Referer (للطلبات القديمة)
    referer = request.headers.get('Referer')
    if referer:
        for bot in ALLOWED_BOTS:
            if referer.startswith(bot):
                return True
    
    # تسجيل محاولة غير مصرح بها
    logger.warning(f"⚠️ Unauthorized request from: {request.headers.get('Origin')} | IP: {request.remote_addr}")
    return False

# =================================================================================
# 🛡️ ديكوراتور لحماية نقاط النهاية API
# =================================================================================
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verify_request():
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': 'مفتاح API غير صالح أو البوت غير مصرح له'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# =================================================================================
# رؤوس الأمان (Security Headers)
# =================================================================================
@app.after_request
def set_security_headers(resp):
    resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # إضافة CORS للبوتات المسموحة
    origin = request.headers.get('Origin')
    if origin in ALLOWED_BOTS:
        resp.headers['Access-Control-Allow-Origin'] = origin
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return resp

# =================================================================================
# نقاط نهاية فحص الصحة (Health Checks)
# =================================================================================
@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "service": "bio-pages",
        "version": "2.0",
        "allowed_bots_count": len(ALLOWED_BOTS)
    }), 200

@app.route('/health')
@app.route('/healthcheck')
def health():
    return jsonify({
        "status": "healthy",
        "service": "bio-pages",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }), 200

# =================================================================================
# 🤖 نقاط نهاية API للبوتات
# =================================================================================

@app.route('/api/verify', methods=['GET', 'POST'])
@require_auth
def api_verify():
    """نقطة نهاية للتحقق من صحة المفتاح"""
    return jsonify({
        'success': True,
        'message': 'API Key is valid',
        'allowed_bots': ALLOWED_BOTS
    }), 200

@app.route('/api/bio/<page_id>', methods=['GET'])
@require_auth
def api_get_bio(page_id):
    """جلب بيانات صفحة البايو عبر API"""
    try:
        bio = get_bio_page_by_page_url(page_id)
        if not bio:
            return jsonify({'success': False, 'error': 'Page not found'}), 404
        
        user_info = get_user_info(bio['user_id'])
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': bio['user_id'],
                'display_name': bio['display_name'],
                'bio': bio.get('bio', ''),
                'avatar_url': bio.get('avatar_url'),
                'theme_name': bio.get('theme_name', 'default'),
                'views_count': bio.get('views_count', 0),
                'email': bio.get('email', ''),
                'phones': [
                    bio.get('phone_1'),
                    bio.get('phone_2'),
                    bio.get('phone_3'),
                    bio.get('phone_4')
                ],
                'custom_links': bio.get('custom_links', []),
                'username': user_info.get('username', '') if user_info else ''
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in api_get_bio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# =================================================================================
# مسار صفحة البايو (Bio Page Route) - العرض العام (بدون حماية للسماح للمستخدمين)
# =================================================================================
@app.route('/bio/<page_url>')
def bio_page(page_url):
    try:
        logger.info(f"🔍 Bio page requested: {page_url}")
        
        bio = get_bio_page_by_page_url(page_url)
        if not bio:
            return "Page not found", 404
            
        user_info = get_user_info(bio['user_id'])
        if not user_info:
            return "User not found", 404
            
        increment_bio_views(page_url)
        
        accounts = bio.get('accounts', {})
        custom_links = bio.get('custom_links', [])
        
        # معالجة custom_links إذا كانت string
        if isinstance(custom_links, str):
            try:
                custom_links = json.loads(custom_links)
            except:
                custom_links = []
        
        platform_icons = {
            'youtube': 'https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg',
            'instagram': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png',
            'tiktok': 'https://upload.wikimedia.org/wikipedia/commons/0/0a/TikTok_logo.svg',
            'facebook': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg'
        }
        platform_names = {
            'youtube': 'YouTube', 'instagram': 'Instagram', 'tiktok': 'TikTok',
            'facebook': 'Facebook', 'snapchat': 'Snapchat'
        }
        
        accounts_list = []
        for platform, acc in accounts.items():
            identifier = acc.get('account_identifier', '')
            if identifier:
                if not identifier.startswith('@'):
                    identifier = '@' + identifier
                
                if platform == 'youtube':
                    url = f"https://youtube.com/{identifier}"
                elif platform == 'instagram':
                    clean = identifier.replace('@', '')
                    url = f"https://instagram.com/{clean}"
                elif platform == 'tiktok':
                    clean = identifier.replace('@', '')
                    url = f"https://tiktok.com/@{clean}"
                elif platform == 'facebook':
                    url = f"https://facebook.com/{identifier}"
                elif platform == 'snapchat':
                    clean = identifier.replace('@', '')
                    url = f"https://snapchat.com/add/{clean}"
                else:
                    url = f"https://{platform}.com/{identifier.replace('@', '')}"
                
                accounts_list.append({
                    'platform': platform,
                    'name': platform_names.get(platform, platform.capitalize()),
                    'url': url,
                    'icon': platform_icons.get(platform, '')
                })
        
        custom_links_list = [
            {'title': link.get('title', 'رابط مخصص'), 'url': link.get('url', '#')}
            for link in custom_links
        ]
        
        # تجهيز أرقام الجوال (تصفية القيم الفارغة)
        raw_phones = [
            bio.get('phone_1'),
            bio.get('phone_2'),
            bio.get('phone_3'),
            bio.get('phone_4')
        ]
        phones = [p for p in raw_phones if p and str(p).strip()]
        
        # تجهيز الإيميل
        email = bio.get('email', '')
        if email:
            email = str(email).strip()
        
        theme_name = bio.get('theme_name', 'default')
        
        return render_template(
            'bio_page.html',
            display_name=bio['display_name'],
            username=user_info.get('username', ''),
            bio=bio.get('bio', ''),
            accounts=accounts_list,
            custom_links=custom_links_list,
            avatar_url=bio.get('avatar_url', None),
            views_count=bio.get('views_count', 0),
            theme_name=theme_name,
            user_id=bio['user_id'],
            is_premium=(user_info.get('status') == 'premium'),
            RENDER_URL=RENDER_URL,
            email=email,
            phones=phones
        )
        
    except Exception as e:
        logger.error(f"Error in bio_page: {e}")
        return f"Internal error: {e}", 500

# =================================================================================
# خدمة الملفات الثابتة
# =================================================================================
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/static/themes/<path:filename>')
def serve_theme(filename):
    return send_from_directory('static/themes', filename)

# =================================================================================
# تشغيل التطبيق
# =================================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 My-Links-in-1 Bio Pages Server - Version 2.0")
    print(f"🤖 Allowed Bots: {len(ALLOWED_BOTS)}")
    for bot in ALLOWED_BOTS:
        if bot.startswith('http'):
            print(f"   ✅ {bot}")
    print(f"🌐 Running on port: {PORT}")
    print(f"🔑 API Key: {'*' * 10}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=PORT, debug=False)
