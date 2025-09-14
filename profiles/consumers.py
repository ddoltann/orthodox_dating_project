import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Получаем ID собеседника из URL
        self.interlocutor_id = self.scope['url_route']['kwargs']['pk']
        self.user = self.scope['user']
        
        # Создаем уникальное имя для комнаты чата
        # Сортируем ID, чтобы имя было одинаковым для обоих пользователей
        user_ids = sorted([int(self.user.id), int(self.interlocutor_id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        # Присоединяемся к группе комнаты
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Отсоединяемся от группы комнаты
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получаем сообщение от WebSocket (от браузера)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        # Сохраняем сообщение в базу данных
        new_message = await self.save_message(message_content)

        # Отправляем сообщение всем в группе комнаты
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': new_message.content,
                'sender_id': new_message.sender.id,
                'timestamp': new_message.timestamp.strftime('%H:%M')
            }
        )
    
    # Обработчик для отправки сообщения обратно в WebSocket (в браузер)
    async def chat_message(self, event):
        # Отправляем сообщение в WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, message_content):
        interlocutor = User.objects.get(id=self.interlocutor_id)
        new_msg = Message.objects.create(
            sender=self.user,
            receiver=interlocutor,
            content=message_content
        )
        return new_msg
