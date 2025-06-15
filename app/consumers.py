from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from urllib.parse import parse_qs

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
            
            # 환영 메시지 전송
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': f'{self.user_name}님, 연결되었습니다!'
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
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception as e:
            logger.error(f"연결 종료 중 오류: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"메시지 수신: {data}")
        except Exception as e:
            logger.error(f"메시지 수신 중 오류: {str(e)}")

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