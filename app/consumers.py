from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from urllib.parse import parse_qs
from django.core.cache import cache
from asgiref.sync import sync_to_async
import time

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
            
            # 기존 사용자인지 확인하고 시간 정보 복원
            if self.user_id in current_users:
                # 기존 사용자 - 기존 정보 유지하되 연결 상태 업데이트
                current_users[self.user_id]['channel_name'] = self.channel_name
                current_users[self.user_id]['connected'] = True
                logger.info(f"기존 사용자 재접속 - {self.user_name}, 기존 시간: {current_users[self.user_id]['timer']}초")
            else:
                # 새 사용자 - 초기 정보 설정
                current_users[self.user_id] = {
                    'user_name': self.user_name,
                    'timer': 0,
                    'present': False,
                    'connected': True,
                    'channel_name': self.channel_name,
                    'last_update_time': time.time()
                }
                logger.info(f"신규 사용자 접속 - {self.user_name}")
            
            # 캐시에 저장
            cache.set(f'room_users_{self.room_id}', current_users, timeout=3600)
            
            # 현재 접속 중인 모든 사용자들의 실시간 시간 계산
            updated_users = await self.calculate_current_times(current_users)
            
            # 현재 접속 중인 유저 목록 전송 (연결된 사용자만)
            connected_users = {uid: data for uid, data in updated_users.items() if data.get('connected', False)}
            await self.send(text_data=json.dumps({
                'type': 'user_list',
                'users': connected_users
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

    async def calculate_current_times(self, users):
        """현재 시점에서 각 사용자의 실제 시간을 계산"""
        current_time = time.time()
        updated_users = {}
        
        for user_id, user_data in users.items():
            updated_users[user_id] = user_data.copy()
            
            # present 상태이고 connected 상태이고 last_update_time이 있는 경우 경과 시간 계산
            if (user_data.get('present', False) and 
                user_data.get('connected', False) and 
                user_data.get('last_update_time')):
                elapsed_time = int(current_time - user_data['last_update_time'])
                updated_users[user_id]['timer'] = user_data.get('timer', 0) + elapsed_time
                updated_users[user_id]['last_update_time'] = current_time
            
        return updated_users

    async def disconnect(self, close_code):
        try:
            logger.info(f"WebSocket 연결 종료 - User: {self.user_name}, Code: {close_code}")
            
            # 현재 접속 중인 유저 목록에서 완전히 제거
            current_users = cache.get(f'room_users_{self.room_id}', {})
            if self.user_id in current_users:
                # 마지막 업데이트 시간으로 현재 시간 계산 후 저장
                if current_users[self.user_id].get('present', False):
                    current_time = time.time()
                    last_update = current_users[self.user_id].get('last_update_time', current_time)
                    elapsed_time = int(current_time - last_update)
                    current_users[self.user_id]['timer'] += elapsed_time
                
                # 사용자 정보 완전 삭제 (재접속을 위한 정보 보존하지 않음)
                final_timer = current_users[self.user_id]['timer']
                del current_users[self.user_id]
                cache.set(f'room_users_{self.room_id}', current_users, timeout=3600)
                
                logger.info(f"사용자 완전 퇴장 - {self.user_name}, 최종 시간: {final_timer}초")
            
            # 다른 사용자들에게 완전 퇴장 알림
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user_id,
                    'user_name': self.user_name,
                    'final_removal': True  # 완전 제거임을 표시
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
            elif data.get('type') == 'fuck':
                await self.handle_fuck_event(data)
                
        except Exception as e:
            logger.error(f"메시지 수신 중 오류: {str(e)}")

    async def handle_presence_update(self, data):
        try:
            user_id = data.get('user_id')
            present = data.get('present', False)
            timer = data.get('timer', 0)
            
            # 현재 접속 중인 유저 목록 업데이트
            current_users = cache.get(f'room_users_{self.room_id}', {})
            current_time = time.time()
            
            if user_id in current_users and current_users[user_id].get('connected', False):
                # 이전 상태가 present였다면 경과 시간 계산
                if current_users[user_id].get('present', False):
                    last_update = current_users[user_id].get('last_update_time', current_time)
                    elapsed_time = int(current_time - last_update)
                    current_users[user_id]['timer'] += elapsed_time
                
                # 새로운 상태 업데이트
                current_users[user_id]['present'] = present
                current_users[user_id]['last_update_time'] = current_time
                
                # 클라이언트에서 보낸 timer 값과 서버에서 계산한 값 중 큰 값 사용
                current_users[user_id]['timer'] = max(current_users[user_id]['timer'], timer)
                
                cache.set(f'room_users_{self.room_id}', current_users, timeout=3600)
                
                logger.info(f"Presence 업데이트 - User: {user_id}, Present: {present}, Timer: {current_users[user_id]['timer']}")
                
                # 다른 사용자들에게 presence 상태 브로드캐스트
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'presence_broadcast',
                        'user_id': user_id,
                        'present': present,
                        'timer': current_users[user_id]['timer'],
                        'exclude_user': user_id
                    }
                )
            else:
                logger.warning(f"연결되지 않은 사용자의 presence 업데이트 시도: {user_id}")
            
        except Exception as e:
            logger.error(f"Presence 업데이트 처리 중 오류: {str(e)}")

    async def handle_fuck_event(self, data):
        try:
            # 모든 클라이언트에게 fuck 이벤트 브로드캐스트
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'fuck_broadcast',
                    'user_id': self.user_id,
                    'user_name': self.user_name
                }
            )
            logger.info(f"Fuck 이벤트 브로드캐스트 - User: {self.user_name}")
            
        except Exception as e:
            logger.error(f"Fuck 이벤트 처리 중 오류: {str(e)}")

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
                'user_name': event['user_name'],
                'final_removal': event.get('final_removal', False)
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

    async def fuck_broadcast(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'fuck_broadcast',
                'user_id': event['user_id'],
                'user_name': event['user_name']
            }))
        except Exception as e:
            logger.error(f"Fuck broadcast 처리 중 오류: {str(e)}")