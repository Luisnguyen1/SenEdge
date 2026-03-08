#!/usr/bin/env python3
"""
Demo script for SenEdge Dashboard Firebase Push Notifications
This script demonstrates the complete workflow:
1. Login to dashboard
2. Register for notifications  
3. Send glass break alerts
4. Monitor notifications
"""

import requests
import json
import time
import sys

class SenEdgeDemo:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def demo_workflow(self):
        """Complete demo workflow"""
        print("🚀 SenEdge Dashboard Firebase Push Notification Demo")
        print("=" * 60)
        
        print("\n📋 Demo Steps:")
        print("1. ✅ Dashboard is running with Firebase integration")
        print("2. 🔐 Login available at: http://localhost:5000/login")
        print("3. 📱 After login, notifications will be auto-requested")
        print("4. 🚨 This script will send glass break alerts")
        print("5. 🔔 You should receive push notifications")
        
        print("\n" + "=" * 60)
        print("🔑 Login Credentials:")
        print("   Username: senedge")
        print("   Password: quyetthang")
        print("=" * 60)
        
        # Wait for user to login
        input("\n📱 Please login to the dashboard first, then press Enter to continue...")
        
        # Test FCM token registration endpoint
        self.test_fcm_status()
        
        # Send glass break alerts
        self.send_demo_alerts()
        
        # Test Firebase notification
        self.test_firebase_notification()
        
    def test_fcm_status(self):
        """Test FCM tokens status"""
        print("\n🔍 Checking FCM tokens status...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/fcm-tokens/status")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ FCM Status: {data.get('notification_system_status', 'unknown')}")
                print(f"📱 Active tokens: {data.get('tokens_count', 0)}")
                print(f"🔔 Firebase initialized: {data.get('firebase_initialized', False)}")
            else:
                print(f"❌ Error checking FCM status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def send_demo_alerts(self):
        """Send demonstration glass break alerts"""
        print("\n🚨 Sending glass break alerts...")
        
        demo_alerts = [
            {
                'device_id': 'DEMO_SENSOR_001',
                'location': 'Main Office - Window 1',
                'severity': 'high',
                'status': 'active'
            },
            {
                'device_id': 'DEMO_SENSOR_002', 
                'location': 'Conference Room A - Glass Door',
                'severity': 'critical',
                'status': 'active'
            },
            {
                'device_id': 'DEMO_SENSOR_003',
                'location': 'Reception Area - Display Case',
                'severity': 'medium',
                'status': 'active'
            }
        ]
        
        for i, alert in enumerate(demo_alerts, 1):
            print(f"\n📤 Sending alert {i}/{len(demo_alerts)}:")
            print(f"   📍 Location: {alert['location']}")
            print(f"   🔴 Severity: {alert['severity']}")
            print(f"   📱 Device: {alert['device_id']}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/security/glass-break",
                    json=alert,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Alert sent successfully")
                    print(f"   🔔 Push notification: {'✅ Sent' if result.get('notification_sent') else '❌ Failed'}")
                else:
                    print(f"   ❌ Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error sending alert: {e}")
            
            # Wait between alerts
            if i < len(demo_alerts):
                print("   ⏳ Waiting 3 seconds...")
                time.sleep(3)
    
    def test_firebase_notification(self):
        """Send test Firebase notification"""
        print("\n🧪 Testing Firebase notification...")
        
        test_data = {
            'title': '🔔 SenEdge Dashboard Test',
            'body': 'This is a test notification from the dashboard demo script!'
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/test-firebase",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test notification sent!")
                print(f"📊 Success: {result.get('success_count', 0)} devices")
                print(f"❌ Failed: {result.get('failure_count', 0)} devices")
                print(f"📱 Total tokens: {result.get('total_tokens', 0)}")
            else:
                print(f"❌ Error sending test notification: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_completion_summary(self):
        """Show completion summary"""
        print("\n" + "=" * 60)
        print("🎉 Demo Completed!")
        print("=" * 60)
        print("\n✅ What was demonstrated:")
        print("   • Firebase Admin SDK integration")
        print("   • FCM token registration after login")
        print("   • Glass break alert processing")
        print("   • Push notification sending")
        print("   • Background notification handling")
        print("   • In-app notification display")
        
        print("\n📱 Expected Results:")
        print("   • Push notifications on your device/browser")
        print("   • In-app notifications on the dashboard")
        print("   • Glass break events stored in database")
        print("   • Real-time dashboard updates")
        
        print("\n🔧 Features Integrated:")
        print("   • Automatic permission request after login")
        print("   • FCM token management")
        print("   • Background/foreground message handling")
        print("   • Glass break alert system")
        print("   • Multi-device notification support")

if __name__ == '__main__':
    demo = SenEdgeDemo()
    
    try:
        demo.demo_workflow()
        demo.show_completion_summary()
        
        print("\n🔄 Additional Testing:")
        print("   • Use test_glass_break.py for more alerts")
        print("   • Check dashboard at http://localhost:5000")
        print("   • Monitor browser console for Firebase logs")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        print("\n👋 Demo finished. Thank you!")