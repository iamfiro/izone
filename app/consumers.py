from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from urllib.parse import parse_qs
from django.core.cache import cache
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'room_{self.room_id}'
            
            # 쿼리 스트링 파싱
            query_string = self.scope['query_string'].decode()
            logger.info(f"WebSocket 연결 시도 - Room ID: {self.room_id}, Query: {query_string}")
            
            if query_string:
                try:
                    query_params = parse_qs(query_string)
                    self.user_id = query_params.get('user_id', [None])[0]
                    self.user_name = query_params.get('user_name', [None])[0]
                    logger.info(f"User ID: {self.user_id}, User Name: {self.user_name}")
                except Exception as e:
                    logger.error(f"쿼리 파라미터 파싱 오류: {str(e)}")
                    self.user_id = "unknown"
                    self.user_name = "unknown"
            else:
                self.user_id = "unknown"
                self.user_name = "unknown"
            
            # 채널 그룹에 추가
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            
            # 연결 수락
            await self.accept()
            logger.info(f"WebSocket 연결 수락됨 - User: {self.user_name}")
            
            # 현재 접속 중인 유저 목록 가져오기
            current_users = cache.get(f'room_users_{self.room_id}', {})
            
            # 현재 유저 정보 추가
            current_users[self.user_id] = {
                'user_name': self.user_name,
                'timer': 0,
                'present': False,
                'channel_name': self.channel_name
            }
            
            # 캐시에 저장
            cache.set(f'room_users_{self.room_id}', current_users, timeout=3600)
            
            # 현재 접속 중인 유저 목록 전송
            await self.send(text_data=json.dumps({
                'type': 'user_list',
                'users': current_users
            }))
            
            # 다른 사용자들에게 입장 알림
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user_id,
                    'user_name': self.user_name,
                    'exclude_user': self.user_id
                }
            )
            
        except Exception as e:
            logger.error(f"WebSocket 연결 중 오류: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            logger.info(f"WebSocket 연결 종료 - User: {self.user_name}, Code: {close_code}")
            
            # 현재 접속 중인 유저 목록에서 제거
            current_users = cache.get(f'room_users_{self.room_id}', {})
            if self.user_id in current_users:
                del current_users[self.user_id]
                cache.set(f'room_users_{self.room_id}', current_users, timeout=3600)
            
            # 다른 사용자들에게 퇴장 알림
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user_id,
                    'user_name': self.user_name
                }
            )
            
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            
        except Exception as e:
            logger.error(f"연결 종료 중 오류: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"메시지 수신: {data}")
            
            if data.get('type') == 'presence_update':
                await self.handle_presence_update(data)
                
        except Exception as e:
            logger.error(f"메시지 수신 중 오류: {str(e)}")

    async def handle_presence_update(self, data):
        try:
            user_id = data.get('user_id')
            present = data.get('present', False)
            timer = data.get('timer', 0)
            
            # 현재 접속 중인 유저 목록 업데이트
            current_users = cache.get(f'room_users_{self.room_id}', {})
            if user_id in current_users:
                current_users[user_id]['present'] = present
                current_users[user_id]['timer'] = timer
                cache.set(f'room_users_{self.room_id}', current_users, timeout=3600)
            
            # 다른 사용자들에게 presence 상태 브로드캐스트
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_broadcast',
                    'user_id': user_id,
                    'present': present,
                    'timer': timer,
                    'exclude_user': user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Presence 업데이트 처리 중 오류: {str(e)}")

    # 메시지 핸들러들
    async def user_joined(self, event):
        try:
            # 자신의 입장 메시지는 무시
            if event.get('exclude_user') == self.user_id:
                return
            
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name']
            }))
        except Exception as e:
            logger.error(f"User joined 처리 중 오류: {str(e)}")

    async def user_left(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'user_name': event['user_name']
            }))
        except Exception as e:
            logger.error(f"User left 처리 중 오류: {str(e)}")

    async def presence_broadcast(self, event):
        try:
            # 자신의 presence 메시지는 무시
            if event.get('exclude_user') == self.user_id:
                return
            
            await self.send(text_data=json.dumps({
                'type': 'presence_broadcast',
                'user_id': event['user_id'],
                'present': event['present'],
                'timer': event['timer']
            }))
        except Exception as e:
            logger.error(f"Presence broadcast 처리 중 오류: {str(e)}")