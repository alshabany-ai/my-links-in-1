# -*- coding: utf-8 -*-
"""
===============================================================================
                       My-Links-in-1 - Bio Pages Server
                                الإصدار 1.0
===============================================================================
الوصف: خادم Flask مخصص لعرض صفحات البايو فقط
الخدمة: https://my-links-in-1.onrender.com
المشروع: Social Media Analyzer Bot
===============================================================================
"""

import os
import logging
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# إعدادات البيئة
PORT = int(os.environ.get('PORT', 10000))
RENDER_URL = os.environ.get('RENDER_URL', 'social-analyzer-flask-3.onrender.com')  # للسيرفر القديم (لتحميل الصور)

# إضافة مجلد utils للمسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد دوال قاعدة البيانات الخاصة بالبايو
from utils.db import get_bio_page_by_page_url, get_user_info, increment_bio_views

app = Flask(__name__)

# =================================================================================
# رؤوس الأمان (Security Headers)
# =================================================================================
@app.after_request
def set_security_headers(resp):
    resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return resp

# =================================================================================
# نقاط نهاية فحص الصحة (Health Checks)
# =================================================================================
@app.route('/')
def home():
    return jsonify({"status": "ok", "service": "bio-pages"}), 200

@app.route('/health')
@app.route('/healthcheck')
def health():
    return jsonify({"status": "ok", "service": "bio-pages"}), 200

# =================================================================================
# مسار صفحة البايو (Bio Page Route)
# =================================================================================
@app.route('/bio/<page_url>')
def bio_page(page_url):
    try:
        logger.info(f"🔍 Bio page requested: {page_url}")
        
        # 1. جلب بيانات الصفحة
        bio = get_bio_page_by_page_url(page_url)
        if not bio:
            return "Page not found", 404
            
        # 2. جلب معلومات المستخدم
        user_info = get_user_info(bio['user_id'])
        if not user_info:
            return "User not found", 404
            
        # 3. زيادة عداد المشاهدات
        increment_bio_views(page_url)
        
        # 4. معالجة الحسابات الاجتماعية
        accounts = bio.get('accounts', {})
        custom_links = bio.get('custom_links', [])
        
        platform_icons = {
            'youtube': 'https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg',
            'instagram': 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png',
            'tiktok': 'https://upload.wikimedia.org/wikipedia/commons/0/0a/TikTok_logo.svg',
            'facebook': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg'
        }
        platform_names = {
            'youtube': 'YouTube',
            'instagram': 'Instagram',
            'tiktok': 'TikTok',
            'facebook': 'Facebook',
            'snapchat': 'Snapchat'
        }
        
        accounts_list = []
        for platform, acc in accounts.items():
            identifier = acc.get('account_identifier', '')
            if identifier:
                if identifier.startswith('@'):
                    identifier = identifier[1:]
                url = f"https://{platform}.com/{identifier}"
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
        
        # 5. عرض القالب
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
            RENDER_URL=RENDER_URL
        )
        
    except Exception as e:
        logger.error(f"Error in bio_page: {e}")
        return f"Internal error: {e}", 500

# =================================================================================
# خدمة الملفات الثابتة
# =================================================================================
@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

@app.route('/static/themes/<path:filename>')
def serve_theme(filename):
    from flask import send_from_directory
    return send_from_directory('static/themes', filename)

# =================================================================================
# تشغيل التطبيق
# =================================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 My-Links-in-1 Bio Pages Server")
    print(f"🌐 Running on port: {PORT}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=PORT, debug=False)