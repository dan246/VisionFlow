# -*- coding: utf-8 -*-
"""
Health Check Routes
Provides health check endpoints for monitoring system status.
"""

from flask import Blueprint, jsonify
from extensions import db
import redis
import os
import psutil
import time
from datetime import datetime

health_bp = Blueprint('health_bp', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'VisionFlow Web API'
    }), 200


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with component status."""
    health_status = {
        'service': 'VisionFlow Web API',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'components': {}
    }
    
    overall_status = True
    
    # Database health check
    try:
        db.session.execute('SELECT 1')
        health_status['components']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        overall_status = False
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Redis health check
    try:
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        r = redis.Redis(host=redis_host, port=redis_port, db=0)
        r.ping()
        health_status['components']['redis'] = {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        overall_status = False
        health_status['components']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
    
    # System resources
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status['components']['system'] = {
            'status': 'healthy',
            'memory_usage_percent': memory.percent,
            'disk_usage_percent': disk.percent,
            'cpu_usage_percent': psutil.cpu_percent()
        }
        
        # Warning thresholds
        if memory.percent > 90 or disk.percent > 90:
            health_status['components']['system']['status'] = 'warning'
            health_status['components']['system']['message'] = 'High resource usage'
        
    except Exception as e:
        health_status['components']['system'] = {
            'status': 'error',
            'message': f'Unable to get system metrics: {str(e)}'
        }
    
    # Set overall status
    if not overall_status:
        health_status['status'] = 'unhealthy'
    elif any(comp.get('status') == 'warning' for comp in health_status['components'].values()):
        health_status['status'] = 'warning'
    
    status_code = 200 if overall_status else 503
    return jsonify(health_status), status_code


@health_bp.route('/health/readiness', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes-style deployments."""
    try:
        # Check if database is ready
        db.session.execute('SELECT 1')
        
        # Check if Redis is ready
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        r = redis.Redis(host=redis_host, port=redis_port, db=0)
        r.ping()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503


@health_bp.route('/health/liveness', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes-style deployments."""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': time.time() - psutil.boot_time()
    }), 200
