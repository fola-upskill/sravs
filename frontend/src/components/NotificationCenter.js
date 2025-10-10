import React, { useState, useEffect } from 'react';
import { webSocketService } from '../services/websocket';

const NotificationCenter = ({ user }) => {
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    if (user) {
      // Connect to WebSocket
      webSocketService.connect(user.role, user.id);
      
      // Add listener for notifications
      const handleNotification = (type, data) => {
        if (type === 'notification') {
          setNotifications(prev => [data, ...prev.slice(0, 49)]); // Keep last 50
          
          // Show browser notification if supported
          if (Notification.permission === 'granted') {
            new Notification('Student Records Update', {
              body: data.message,
              icon: '/favicon.ico'
            });
          }
        } else if (type === 'connected') {
          setIsConnected(true);
        } else if (type === 'disconnected') {
          setIsConnected(false);
        }
      };
      
      webSocketService.addListener(handleNotification);
      
      // Request notification permission
      if (Notification.permission === 'default') {
        Notification.requestPermission();
      }
      
      return () => {
        webSocketService.removeListener(handleNotification);
        webSocketService.disconnect();
      };
    }
  }, [user]);

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'new_request':
        return '📋';
      case 'verification_complete':
        return '✅';
      case 'request_approved':
        return '👍';
      case 'request_rejected':
        return '❌';
      case 'blockchain_confirmed':
        return '🔗';
      default:
        return '📢';
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'new_request':
        return 'bg-blue-50 border-blue-200';
      case 'verification_complete':
        return 'bg-green-50 border-green-200';
      case 'request_approved':
        return 'bg-green-50 border-green-200';
      case 'request_rejected':
        return 'bg-red-50 border-red-200';
      case 'blockchain_confirmed':
        return 'bg-purple-50 border-purple-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatTime = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now - time) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return time.toLocaleDateString();
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:text-gray-900"
      >
        <svg className="w-6 h-6" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
        </svg>
        
        {/* Notification Badge */}
        {notifications.length > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {notifications.length > 99 ? '99+' : notifications.length}
          </span>
        )}
        
        {/* Connection Status */}
        <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
      </button>

      {/* Notification Dropdown */}
      {showNotifications && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
          <div className="py-1 max-h-96 overflow-y-auto">
            <div className="px-4 py-2 text-sm font-medium text-gray-900 bg-gray-50 border-b">
              Notifications
              {isConnected && <span className="ml-2 text-xs text-green-600">● Live</span>}
            </div>
            
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2 2v-5m16 0h-2M4 13h2m13-4v1M7 9v1" />
                </svg>
                <p className="mt-2 text-sm">No notifications yet</p>
                <p className="text-xs text-gray-400">You'll see updates here when they arrive</p>
              </div>
            ) : (
              notifications.map((notification, index) => (
                <div
                  key={index}
                  className={`px-4 py-3 hover:bg-gray-50 border-l-4 ${getNotificationColor(notification.type)}`}
                >
                  <div className="flex items-start">
                    <span className="text-lg mr-3 mt-0.5">
                      {getNotificationIcon(notification.type)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatTime(notification.timestamp)}
                      </p>
                      
                      {/* Additional notification data */}
                      {notification.data && notification.data.action_required && (
                        <div className="mt-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Action Required
                          </span>
                        </div>
                      )}
                      
                      {notification.data && notification.data.blockchain_verified && (
                        <div className="mt-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            🔗 Blockchain Verified
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          {notifications.length > 0 && (
            <div className="px-4 py-2 bg-gray-50 border-t">
              <button
                onClick={() => setNotifications([])}
                className="text-xs text-gray-600 hover:text-gray-900"
              >
                Clear all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;