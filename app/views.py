from django.shortcuts import render, redirect, get_object_or_404
from .models import Room
from .forms import RoomForm

# 방 생성
def create_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('select_room')  # 방 선택 페이지로 이동
    else:
        form = RoomForm()
    return render(request, 'create_group.html', {'form': form})

# 방 선택
def select_room(request):
    rooms = Room.objects.all()
    return render(request, 'select_room.html', {'rooms': rooms})

# 방 내부
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'room.html', {'room': room})