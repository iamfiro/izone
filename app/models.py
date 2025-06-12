from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=100)  # 방 이름
    description = models.TextField(blank=True, null=True)  # 방 설명
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간

    def __str__(self):
        return self.name