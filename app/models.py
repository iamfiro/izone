from django.db import models
from user.models import CustomUser

class RoomUser(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # 유저 정보
    timer = models.IntegerField(default=0) # 타이머 시간
    joined_at = models.DateTimeField(auto_now_add=True) # 방에 들어온 시간
    is_host = models.BooleanField(default=False) # 방장인지? (방잠이면 삭제 권한)

class Room(models.Model):
    name = models.CharField(max_length=100)  # 방 이름
    description = models.TextField(blank=True, null=True)  # 방 설명
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    room_users = models.ManyToManyField(RoomUser, related_name='rooms') # 방에 속한 유저들

    def __str__(self):
        return self.name