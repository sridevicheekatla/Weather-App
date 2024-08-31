from django.shortcuts import render
import requests

from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import Avg

from .models import WeatherData



def weather_analysis(request):
    api_key = getattr(settings, 'WEATHER_API_KEY', None)
    context = {'message': '', 'message_class': ''}       
    
    if request.method == 'POST':
        city = request.POST.get('city')        
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            WeatherData.objects.create(
                city=data['location']['name'],
                temperature=data['current']['temp_c'],
                humidity=data['current']['humidity'],
                condition=data['current']['condition']['text'],
            )
            
            city_data = WeatherData.objects.filter(
                city=city,
                timestamp__gte=timezone.now() - timedelta(days=1),
            )
            if city_data.exists():
                avg_temp = city_data.aggregate(avg_temp=Avg('temperature'))['avg_temp']
                avg_hum = city_data.aggregate(avg_hum=Avg('humidity'))['avg_hum']
                
                if avg_temp > 30 or avg_temp < 0 or avg_hum > 75 or avg_hum < 0:
                    context['message'] = (
                        f"Average temperature in the last 24 hours: {avg_temp:.2f}°C, "
                        f"Average humidity: {avg_hum:.2f}%"
                    )
                    context['message_class'] = 'alert-danger'
            
            context.update({
                'city': data['location']['name'],
                'temperature': data['current']['temp_c'],
                'humidity': data['current']['humidity'],
                'condition': data['current']['condition']['text'],
            })

        else:
            context['message'] = "City doesnt exist"
            context['message_class'] = 'alert-warning'
    
    return render(request, 'weather.html', context)
