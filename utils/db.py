# -*- coding: utf-8 -*-
"""
دوال قاعدة البيانات الخاصة بصفحات البايو فقط
للاستخدام في سيرفر my-links-in-1.onrender.com
"""

import os
import logging
import hashlib
import random
import string
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# ========== إعدادات Supabase ==========
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")

# عميل عام (قراءة فقط)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =================================================================================
# دوال المستخدمين (قراءة فقط)
# =================================================================================

def get_user_info(user_id):
    """جلب معلومات المستخدم"""
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None


# =================================================================================
# دوال صفحة البايو (قراءة فقط - supabase)
# =================================================================================

def get_bio_page_by_page_url(page_url):
    """جلب صفحة البايو بواسطة page_url (قراءة فقط)"""
    try:
        response = supabase.table('bio_pages')\
            .select('*')\
            .eq('page_url', page_url)\
            .eq('is_enabled', True)\
            .execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error getting bio page by url: {e}")
        return None


def increment_bio_views(page_url):
    """زيادة عدد مشاهدات صفحة البايو"""
    try:
        # جلب العدد الحالي
        response = supabase.table('bio_pages')\
            .select('views_count')\
            .eq('page_url', page_url)\
            .execute()
        
        if response.data:
            current_views = response.data[0].get('views_count', 0)
            new_views = current_views + 1
            
            # تحديث العدد
            supabase.table('bio_pages').update({
                'views_count': new_views
            }).eq('page_url', page_url).execute()
            
            logger.info(f"👁️ Bio view incremented for {page_url}: {new_views}")
        
        return True
    except Exception as e:
        logger.error(f"Error incrementing bio views: {e}")
        return False